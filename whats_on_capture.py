#!/usr/bin/python
# vim: set fileencoding=utf-8 :

"""Scrapes websvc and adds them to SimpleDB"""

from __future__ import print_function
import boto
import datetime
import re
import pytz
import sys
import urllib
import collections
import yaml
import lastfm_utils
import pylast
import ConfigParser
import os


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
  
    lastfm = lastfm_utils.get_lastfm_conn()

    if lastfm is None:
        sys.exit(-1)

    try:
        stations_yaml = open('stations.yaml')
    except IOError:
        print("Failed to load station list", file=sys.stderr)
        sys.exit(-1)
  
    stations = yaml.load(stations_yaml)
  
    sdb = boto.connect_sdb()

    queried_songs = {}

    for key, value in stations.items():
        # if key != 'CJZN':
        #     continue

        print("Scraping", key)

        scrape_station( key, 
                        URL % (key, value['id']), 
                        POST, 
                        value['tz'], 
                        sdb, 
                        lastfm,
                        queried_songs )
  
    print(datetime.datetime.now())


def store_in_cloud_db( domain, plays, lastfm, queried_songs ):
    """Stores a play list in a SimpleDB domain
  
    Existing plays will be queried to see if the album has already been defined.
  
    Keywork arguments:
    domain -- the SimpleDB domain to store it in
    plays  -- a dict with keys representing timestamps, the value is a tuple (artist, title)
  
    """
    items = {}
    total = 0
  
    for epoch, attrs in plays.items():

        play = {'Artist': attrs[0], 'Title': attrs[1]}

        if attrs in queried_songs:
            item_attrs = queried_songs[attrs]
        else:
            track_info = lastfm_utils.get_lastfm_track_info(play,
                                                            lastfm)
            item_attrs = play

            if track_info:
                for key in ['Album', 'MBID', 'LFID']:
                    if key in track_info:
                        item_attrs[key] = track_info[key]

            # Cache play info for next time
            queried_songs[attrs] = item_attrs

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


def get_plays( times, url, post_base ):
    """

    Returns an OrderedDict of key = epoch, value = (artist, song)

    """

    plays = collections.OrderedDict()
  
    #i = 0
  
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
        #if i == 10:
        #  break
    
        #i += 1

    return plays

def scrape_station( station, url, post, timezone, sdb, lastfm, queried_songs ):

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
        plays = get_plays( filtered_times, url, post )

        if plays:
            store_in_cloud_db( domain, plays, lastfm, queried_songs )


if __name__ == "__main__":
    main()
