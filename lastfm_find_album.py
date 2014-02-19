#!/usr/bin/python

"""Queries the databases for songs without albums recorded, and queries
Last.fm for the album. This is done as a separate process, as the
Last.fm API limits how fast you can grab data from it."""

from __future__ import print_function
import boto
import time
import datetime
import yaml
import sys
import os
import pylast
import ConfigParser

SONGS_PER_DOMAIN = 100

def main():
    """Looks for songs without an album attribute and fills them in
    via Last.fm"""
    print(datetime.datetime.now())

    try:
        stations_yaml = open('stations.yaml')
    except IOError:
        print("Failed to load station list", file=sys.stderr)
        sys.exit(-1)

    stations = yaml.load(stations_yaml)

    sdb = boto.connect_sdb()

    config = ConfigParser.ConfigParser()

    cfg_file = '.lastfm'
    if not os.path.isfile(cfg_file) or (config.read(cfg_file)[0] != cfg_file):
        print("Error reading config file")
        sys.exit(-1)

    username      = config.get('Credentials', 'username')
    password_hash = config.get('Credentials', 'password_hash')
    api_key       = config.get('Credentials', 'api_key')
    api_secret    = config.get('Credentials', 'api_secret')

    try:
        lastfm = pylast.LastFMNetwork(api_key = api_key, api_secret = 
                api_secret, username = username, password_hash = password_hash)
    except pylast.WSError as error:
        print("Failed to log in:", error)
        sys.exit(-1)

    for station_id in stations.keys():
        get_empty_album_plays( station_id, sdb )
    while True:
        for station_id in stations.keys():
            print("Checking ", station_id)
            if not add_album_attribute( station_id, sdb, lastfm ):
                del stations[station_id]
        if not len(stations):
            break

    print(datetime.datetime.now())

def get_empty_album_plays( station, sdb ):
    domain = sdb.get_domain("%s-whatson" % station )

    query = 'select count(*) from `%s-whatson` where Album is null' \
            % (station)
    result_set = domain.select(query, max_items=1)
    for item in result_set:
        print(item['Count'], "songs needing albums from", station)


def add_album_attribute( station, sdb, lastfm ):
    """Adds Album attribute for plays where it is not already set.

    Arguments:

    station -- Station ID
    sdb -- SimpleDB connection

    Returns the number of plays that were updated.

    """

    count = 0

    domain = sdb.get_domain("%s-whatson" % station )

    query = 'select count(*) from `%s-whatson` where Album is null' \
            % (station)
    result_set = domain.select(query, max_items=1)
    for item in result_set:
        # print(item['Count'], "songs needing albums from", station)
        count = int(item['Count'])

    # Get a list of items from the domain that don't have an album 
    # attribute
    #
    # Find its album name
    #
    # Find all of the songs with that title/artist, and update with
    # the album

    query = 'select * from `%s-whatson` where Album is null limit %d' \
                % (station, SONGS_PER_DOMAIN)
    result_set = domain.select(query, max_items=SONGS_PER_DOMAIN)

    # TODO: FIXME: Move this to above the station loop so we cache globally,
    # not per station
    queried_songs = {}

    for item in result_set:
        if (item['Artist'], item['Title']) in queried_songs:
            # print(item['Artist'], item['Title'], "has already been found")
            continue

        album = find_album_name(item, lastfm)

        queried_songs[(item['Artist'], item['Title'])] = album

        if album == "":
            # print("No album found for", item)
            continue

        print("Album for ", item, "is", album)

        artist = item['Artist'].replace('"', '""')
        title = item['Title'].replace('"', '""')
        song_query = 'select * from `%s-whatson` where Title = "%s" '\
                     'and Artist = "%s" and Album is NULL' \
                     % (station, title, artist)
        song_rs = domain.select(song_query)
        for song in song_rs:
            song_item = domain.get_item(song.name)
            print("Updating", song_item.name, song_item)
            song_item['Album'] = album
            song_item.save()
    
    return count != 0


def find_album_name( track_details, lastfm ):

    album = ""

    # Last.fm limits API calls to five per second from a specific IP
    time.sleep(0.2)

    try:
        track = lastfm.get_track(track_details['Artist'],
                                 track_details['Title'])
        if track is not None:
            try:
                lastfm_album = track.get_album()
            except pylast.MalformedResponseError:
                lastfm_album = None
                # print("Malformed response", track_details)

            if lastfm_album is not None:
                album = lastfm_album.get_title()
            else:
                #print("Album not in database", track_details)
                pass
        else:
            #print("Track not in database", track_details)
            pass
    except pylast.WSError as error:
        print("Track not found:", error, track_details)

    return album


if __name__ == "__main__":
    main()
