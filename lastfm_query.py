#!/usr/bin/python
"""Small utility to show track details"""

from __future__ import print_function
import datetime
import pylast
import sys
import os
import ConfigParser


def main():
    """Small utility to show track details

    Useful for debugging tracks with missing albums and LFIDs

    """

    print(datetime.datetime.now())

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
        network = pylast.LastFMNetwork(api_key = api_key, api_secret = 
                api_secret, username = username, password_hash = password_hash)
    except pylast.WSError as error:
        print("Failed to log in:", error)
        sys.exit(-1)

    artist = u'Fefe Dobson'
    title = u"Stuttering"

    try:
        track = network.get_track(artist, title)
        print(track)
        print(track.get_album())
        print(track.get_artist())
    except pylast.WSError as error:
        print("Track not found:", error)


    print(datetime.datetime.now())


if __name__ == "__main__":
    main()
