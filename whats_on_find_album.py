#!/usr/bin/python
# vim: set fileencoding=utf-8 :

"""Queries the databases for songs without albums recorded, and queries
Musicbrainz for the album. This is done as a separate process, as the
Musicbrainz API limits how fast you can grab data from it."""

from __future__ import print_function
import boto
import time
import datetime
import yaml
import sys
from musicbrainz2.webservice import Query, TrackFilter, WebServiceError, \
      AuthenticationError, ConnectionError, RequestError, ResponseError, \
      ResourceNotFoundError
from musicbrainz2.model import Release


SONGS_PER_DOMAIN = 100

def main():
    """Looks for songs without an album attribute and fills them in
    via Musicbrainz"""
    print(datetime.datetime.now())

    try:
        stations_yaml = open('stations.yaml')
    except IOError:
        print("Failed to load station list", file=sys.stderr)
        sys.exit(-1)

    stations = yaml.load(stations_yaml)

    sdb = boto.connect_sdb()

    while True:
        for station_id in stations.keys():
            print("Checking ", station_id)
            if not add_album_attribute( station_id, sdb ):
                del stations[station_id]
        if not len(stations):
            break

    print(datetime.datetime.now())

def add_album_attribute( station, sdb ):
    """Adds Album attribute for plays where it is not already set.

    Arguments:

    station -- Station ID
    sdb -- SimpleDB connection

    Returns the number of plays that were updated.

    """


    count = 0

    domain = sdb.get_domain("%s-whatson" % station )

    query = 'select count(*) from `%s-whatson` where `Album` is null' \
            % (station)
    result_set = domain.select(query, max_items=1)
    for item in result_set:
        print(item['Count'], "songs needing albums from", station)
        count = item['Count']

    # Get a list of items from the domain that don't have an album 
    # attribute
    #
    # Find its album name
    #
    # Find all of the songs with that title/artist, and update with
    # the album

    query = 'select * from `%s-whatson` where `Album` is null limit %d' \
                % (station, SONGS_PER_DOMAIN)
    result_set = domain.select(query, max_items=SONGS_PER_DOMAIN)
    for item in result_set:
        album = find_album_name(item)
        print("Album for ", item, "is", album)
        if album == "":
            continue

        artist = item['Artist'].replace('"', '""')
        title = item['Title'].replace('"', '""')
        song_query = 'select * from `%s-whatson` where `Title` = "%s" '\
                     'and `Artist` = "%s" and `Album` is not NULL' \
                     % (station, title, artist)
        song_rs = domain.select(song_query)
        for song in song_rs:
            song_item = domain.get_item(song.name)
            # print("Updating", item.name, item)
            song_item['Album'] = album
            song_item.save()
    
    return count != 0


def find_album_name( track_details ):
    """Find album name via Musicbrainz API

    Arguments:

    track_details -- dict containing 'Title' and 'Artist'

    Returns album name, empty string if unsuccessful.

    """

    album = ""

    # Musicbrainz limits API calls to one per second from a specific IP
    time.sleep(1.1)

    query = Query()

    # Loop through at most 9 times as the webservice is occasionally busy.
    # Results will not be None if is successful
    i = 1
    results = None
    while (results == None) and (i < 10):
        try:
            tracks = TrackFilter(title=track_details['Title'], 
                                 artistName=track_details['Artist'])
            results = query.getTracks(tracks)
        except (AuthenticationError,
                ConnectionError,
                RequestError,
                ResponseError,
                ResourceNotFoundError,
                WebServiceError) as error:
            print('Error:', error, 'waiting', i*10, 'seconds')
            time.sleep(i*10)
            i += 1
            results = None

    if (results != None) and (len(results) != 0):
        album = find_preferred_album( results )

    return album


def find_preferred_album( results ):
    """Find the most likely to be reasonable name of the album
    
    Arguments:
    
    results -- result of a Musicbrainz query

    Returns an album string. Empty if unsuccessful.
    """

    # TODO: FIXME: Musicbrainz results are not returning a date
    # associated with a release. Would prefer to use the oldest
    # album if possible.

    found_release = None
    release_type = None
    release = None

    for result in results:

        track = result.track

        # Prefer: album, single, live, anything else

        for release in track.releases:
            if Release.TYPE_ALBUM in release.getTypes():
                found_release = release
                release_type = Release.TYPE_ALBUM
                break
            elif Release.TYPE_SINGLE in release.getTypes():
                if release_type != Release.TYPE_ALBUM:
                    found_release = release
                    release_type = Release.TYPE_SINGLE
            elif Release.TYPE_LIVE in release.getTypes():
                if release_type != Release.TYPE_ALBUM and \
                    release_type != Release.TYPE_SINGLE:
                    found_release = release
                    release_type = Release.TYPE_LIVE
            else:
                if release_type != Release.TYPE_ALBUM and \
                    release_type != Release.TYPE_SINGLE and \
                    release_type != Release.TYPE_LIVE:
                    found_release = release

        if release_type == Release.TYPE_ALBUM:
            break

    if found_release == None:
        album = ""
    else:
        album = release.title

    return album


if __name__ == "__main__":
    main()
