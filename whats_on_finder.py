#!/usr/bin/python

"""Scans the websvc page for station ids"""

from __future__ import print_function
import time
import datetime
import re
import urllib

URL = 'http://websvc.bdsrealtime.com/NBDS.Consumer.Tempo/' \
      'nowplaying.aspx?stnid=%04d'
POST = '__EVENTTARGET=detectTime&__EVENTARGUMENT=&detectTime='

def main():
    """Scans the websvc page and reports station ids that return valid data"""
    print(datetime.datetime.now())
  
    for station_id in range(0, 10000):
        print("Looking for %d" % station_id,)
        scrape_station( URL % station_id, POST )
  
    print(datetime.datetime.now())


def get_timestamps( source ):
    """Gets timestamps from a websvc formatted web page"""
  
    song_times = re.findall('<option value=\"(.*?)\">(.*?)<\/option>',
                            source)
    if ( len(song_times) != 0 ):
        print(song_times[0][0])
    else:
        print("")


def scrape_station( url, post ):
    """Grabs the page from the url and scans it for timestamps"""
  
    try:
        url_source = urllib.urlopen(url, post)
    except IOError as error:
        print("Error reading URL:", error)
        return
      
    source = url_source.read()
    url_source.close()
  
    time.sleep(1)
  
    get_timestamps( source )

if __name__ == "__main__":
    main()
