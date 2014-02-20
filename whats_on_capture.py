#!/usr/bin/python

"""Scrapes websvc and adds them to SimpleDB"""

from __future__ import print_function
import boto
import time
import datetime
import re
import pytz
import sys
import urllib
import collections
import yaml
from musicbrainz2.webservice import Query, TrackFilter, WebServiceError, \
                                    AuthenticationError, ConnectionError, \
                                    RequestError, ResponseError, \
                                    ResourceNotFoundError
from musicbrainz2.model import Release


# TODO:
#
# * dynamically discover timezone
# * add station name in yaml


#    8 bytes for timestamp
#    5 for title
#    6 for artist
#   10 average for song title
#   10 average for artist name
#   --
#   39 total bytes per record
# x 34 stations
#   --
#
#  1,326 bytes
#
#  24 * 60 minutes in a day = 1440
#
#  3 minutes per song
#
#  ---
#
#        480 songs per day
# x    1,326
#  --------- 
#    636,480 bytes per day
#       x 30
#  ---------
# 19,094,400 bytes per month

URL = 'http://websvc.bdsrealtime.com/NBDS.Consumer.Tempo/' \
      'nowplaying.aspx?uid=Service%s&stnid=%04d'
POST = '__EVENTTARGET=detectTime&__EVENTARGUMENT=&detectTime='

def main():
    """Loops through all stations and scrapes the most recent songs"""
  
    print(datetime.datetime.now())
  
    try:
        stations_yaml = open('stations.yaml')
    except IOError:
        print("Failed to load station list", file=sys.stderr)
        sys.exit(-1)
  
    stations = yaml.load(stations_yaml)
  
    for key, value in stations.items():
        scrapeStation( key, URL % (key, value['id']), POST, value['tz'] )
  
    print(datetime.datetime.now())


def store_in_cloud_db( domain, plays ):
    """Stores a play list in a SimpleDB domain
  
    Existing plays will be queried to see if the album has already been defined.
  
    Keywork arguments:
    domain -- the SimpleDB domain to store it in
    plays  -- a dict with keys representing timestamps, the value is a tuple (artist, title)
  
    """
    items = {}
    total = 0
  
    for epoch, attrs in plays.items():
        artist = attrs[0].replace('"', '""')
        title = attrs[1].replace('"', '""')

        # Check for Album attribute set
        song_query = 'select * from `%s` where (`Album` is not NULL or `No_Album` is not NULL) ' \
                     'and `Artist` = "%s" and `Title` = "%s"' \
                     % (domain.name, artist, title)
    
        song_rs = domain.select(song_query, max_items=1)
        album = None
        for song in song_rs:
            album = song['Album']
            no_album = song['No_Album']
        if (album is not None and album is not "") or (no_album is not None):
            # TODO: FIXME: Query all domains, not just the current station
            item_attrs = {'Artist': attrs[0],
                          'Title': attrs[1],
                          'Album': album,
                          'No_Album': no_album}
            #print("Found existing album", album, "for", attrs)
        else:
            item_attrs = {'Artist': attrs[0], 'Title': attrs[1]}
            #print("Could not find album for", attrs)
        items["%08x" % epoch] = item_attrs
    
        if len(items) == 20:
            domain.batch_put_attributes(items)
            items = {}
            total += 20
    else:
        if len(items) != 0:
            domain.batch_put_attributes(items)
            total += len(items)
  
    print("Songs inserted: ", total)



def get_last_song_time( domain ):
    """Gets the timestamp of the last song played in a domain"""

    query = 'select * from `%s` where itemName() > "00000000" ' \
            'order by itemName() desc limit 1' % (domain.name)
    result_set = domain.select(query, max_items=1)
  
    for item in result_set:
        print(domain.name, item.name, item)
        try:
            last_song_time = int(item.name, 16)
            break
        except ValueError:
            invalid_item = domain.get_item(item.name)
            print("Deleting", item.name)
            domain.delete_item( invalid_item )
        # print("Last song: ", int(item.name, 16), ":", item)
    else:
        last_song_time = 0
  
    return last_song_time



def get_timestamps( source, timezone ):

    timestamps = collections.OrderedDict()
  
    song_times = re.findall('<option value=\"(.*?)\">(.*?)<\/option>',
                            source)
    if ( len(song_times) == 0 ):
        return timestamps
  
    # Get the station's current time
    then = datetime.datetime(1970, 1, 1)
    then = pytz.UTC.localize(then)
    then = then.astimezone(pytz.timezone(timezone))
  
    station_time = datetime.datetime.now(pytz.timezone(timezone))
  
    station_epoch = (station_time - then).total_seconds()
  
    for song_time in reversed(song_times):
        # Convert song time to 'current time'
        is_pm = song_time[0][-2:] == 'PM'
        hour, minute = song_time[0][:-2].split(':')
        hour = int(hour)
        minute = int(minute)
    
        # If we are 1:00PM and greater
        if is_pm and hour != 12:
            hour += 12
    
        # If we are 12:00AM - 12:59AM
        if not is_pm and hour == 12:
            hour = 0
    
        song_dt = station_time.replace(hour=hour, minute=minute,
                                        second=0, microsecond=0)
        song_epoch = int((song_dt - then).total_seconds())
    
        if song_epoch > station_epoch:
            song_epoch -= 24*60*60
    
        timestamps[song_epoch] = song_time[0]
  
    return timestamps

def getSongInfo( plays ):
    detailed_plays = collections.OrderedDict()
  
    for k,v in plays.items():
  
        q = Query()
        time.sleep(1.1)
    
        found = False
        i = 1
        while not found and i < 10:
            try:
                f = TrackFilter(title=v[1], artistName=v[0])
                results = q.getTracks(f)
                found = True
            except (AuthenticationError,
                    ConnectionError,
                    RequestError,
                    ResponseError,
                    ResourceNotFoundError,
                    WebServiceError) as error:
                detailed_plays[k] = (v[0], v[1], "")
                print('Error:', error, 'waiting', i*10, 'seconds')
                results = None
                time.sleep(i*10)
                i += 1
    
    
        if (results != None) and (len(results) != 0):
    
            found_release = None
            release_type = None
            release = None
    
            for result in results:
    
                track = result.track
                title = track.title
                artist = track.artist.name
    
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
    
            detailed_plays[k] = (artist, title, album)
        else:
            detailed_plays[k] = (v[0], v[1], "")

    return detailed_plays


def getPlays( times, url, post_base ):
    plays = collections.OrderedDict()
  
    # i = 0
  
    for epoch, url_time_str in times.iteritems():
        post = post_base + url_time_str.replace(':', '%3A')
        try:
            websvc_source = urllib.urlopen(url, post)
        except IOError as error:
            print("Error reading URL:", error)
            sys.exit(1)

        source = websvc_source.read()
        websvc_source.close()
    
        artist = re.findall('<span id=\"detectArtist\">(.*?)<\/span>', source)
        song = re.findall('<span id=\"detectSong\">(.*?)<\/span>', source)
    
        plays[epoch] = (artist[0], song[0])
    
        # Limit accesses per run:
        # if i == 10:
        #   break
    
        # i += 1

    return plays

def scrapeStation( station, url, post, timezone ):
    sdb = boto.connect_sdb()

    domain = sdb.create_domain("%s-whatson" % station )

    try:
        websvc_source = urllib.urlopen(url, post)
    except IOError as error:
        print("Error reading URL:", error)
        sys.exit(1)
      
    source = websvc_source.read()
    websvc_source.close()

    times = get_timestamps( source, timezone )

    last_song_time = get_last_song_time( domain )
    # print(last_song_time)

    # Filter anything older than last song time
    # TODO OrderedDict list comprehension
    filtered_times = collections.OrderedDict()
    for key, value in times.items():
        if key > last_song_time:
            filtered_times[key] = value

    if times:
        plays = getPlays( filtered_times, url, post )

        if plays:
            store_in_cloud_db( domain, plays )


if __name__ == "__main__":
    main()
