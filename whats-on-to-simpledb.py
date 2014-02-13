#!/usr/bin/python

import boto
import time
import datetime
import re
import pytz
import sys
import urllib
import pprint
import collections
import yaml

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

URL = 'http://websvc.bdsrealtime.com/NBDS.Consumer.Tempo/nowplaying.aspx?uid=Service%s&stnid=%04d'
POST = '__EVENTTARGET=detectTime&__EVENTARGUMENT=&detectTime='

def main():
  print datetime.datetime.now()

  # FIXME: TODO: Handle missing file
  f = open('stations.yaml')
  stations = yaml.load(f)

  for k,v in stations.items():
    scrapeStation( k, URL % (k, v['id']), POST, v['tz'] )

  print datetime.datetime.now()


def storeInCloudDB( domain, plays ):
  items = {}
  total = 0

  for epoch, attrs in plays.items():
    item_attrs = {'Artist': attrs[0], 'Title': attrs[1]}
    items["%08x" % epoch] = item_attrs

    if len(items) == 20:
      domain.batch_put_attributes(items)
      items = {}
      total += 20
  else:
    if len(items) != 0:
      domain.batch_put_attributes(items)
      total += len(items)

  print "Songs inserted: ", total



def getLastSongTime( station, domain ):
  query = 'select * from `%s-whatson` where itemName() > "00000000" order by itemName() desc limit 1' % (station)
  rs = domain.select(query, max_items=1)

  for j in rs:
    last_song_time = int(j.name, 16)
    # print "Last song: ", int(j.name, 16), ":", j
    break
  else:
    last_song_time = 0

  return last_song_time



def getTimestamps( source, timezone ):

  timestamps = collections.OrderedDict()

  song_times = re.findall('<option value=\"(.*?)\">(.*?)<\/option>', source)
  if ( len(song_times) == 0 ):
    return timestamps

  # Get the station's current time
  then = datetime.datetime(1970,1,1)
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

    song_dt = station_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
    song_epoch = int((song_dt - then).total_seconds())

    if song_epoch > station_epoch:
      song_epoch -= 24*60*60

    timestamps[song_epoch] = song_time[0]

  return timestamps


def getPlays( times, url, post_base ):
  plays = collections.OrderedDict()

  i = 0

  for epoch, url_time_str in times.iteritems():
    post = post_base + url_time_str.replace(':', '%3A')
    fh = urllib.urlopen(url, post)
    source = fh.read()
    fh.close()

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
    fh = urllib.urlopen(url, post)
  except:
    print "Error reading URL"
    sys.exit(1)
    
  source = fh.read()
  fh.close()

  times = getTimestamps( source, timezone )

  last_song_time = getLastSongTime( station, domain )
  # print last_song_time

  # Filter anything older than last song time
  # TODO OrderedDict list comprehension
  filtered_times = collections.OrderedDict()
  for k,v in times.items():
    if k > last_song_time:
      filtered_times[k] = v

  if times:
    plays = getPlays( filtered_times, url, post )

  # pprint.pprint( plays )

    if plays:
      storeInCloudDB( domain, plays )


if __name__ == "__main__":
  main()
