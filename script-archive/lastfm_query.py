#!/usr/bin/python
# vim: set fileencoding=utf-8 :
"""Small utility to show track details"""

from __future__ import print_function
import datetime
import pylast
import sys
import lastfm_utils


def main():
    """Small utility to show track details

    Useful for debugging tracks with missing albums and LFIDs

    """

    print(datetime.datetime.now())
    lastfm = lastfm_utils.get_lastfm_conn()
    if lastfm is None:
        sys.exit(-1)

    artist = u'Future Fambo feat. Beenie Man'
    title = u"Rum & Red Bull"

    try:
        track = lastfm.get_track(artist, title)
        print(track)
        print(track.get_album())
        print(track.get_artist())
    except pylast.WSError as error:
        print("Track not found:", error)


    print(datetime.datetime.now())


if __name__ == "__main__":
    main()
