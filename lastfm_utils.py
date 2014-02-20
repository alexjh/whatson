#!/usr/bin/python

"""Queries the databases for songs without albums recorded, and queries
Last.fm for the album. This is done as a separate process, as the
Last.fm API limits how fast you can grab data from it."""

from __future__ import print_function
import time
import datetime
import sys
import os
import pylast
import ConfigParser
import whats_on_translate

VERBOSE = False

def main():
    """Looks for songs without an album attribute and fills them in
    via Last.fm"""
    print(datetime.datetime.now())

    lastfm = get_lastfm_conn()
    if lastfm is None:
        sys.exit(-1)

    tracks = [
               {'Artist': 'Foo Fighters', 'Title': 'Monkey Wrench'}, # Good
               {'Artist': 'Trooper', 
                'Title': 'The Boys In The Bright White Sports Cars'}, # Override
               {'Artist': 'Prince', 'Title': '- 1999 -'}, # Override
               {'Artist': 'Glenn Morrison feat. Islove',
                'Title': 'Goodbye'}, # Valid track, no album
               {'Artist': 'qe7wuyeS', 'Title': 'tHaw6Seq'}, # Invalid
             ]

    for track in tracks:
        track_info = get_lastfm_track_info( track, lastfm )
        print(track_info)

  
    print(datetime.datetime.now())

def get_lastfm_conn(cfg_file = '.lastfm'):
    """Acquires a lastfm network connection
    
    Returns a connection if successful, None if it failed
    
    """
    lastfm = None

    config = ConfigParser.ConfigParser()

    if not os.path.isfile(cfg_file) or (config.read(cfg_file)[0] != cfg_file):
        print("Error reading config file")
    else:
        username      = config.get('Credentials', 'username')
        password_hash = config.get('Credentials', 'password_hash')
        api_key       = config.get('Credentials', 'api_key')
        api_secret    = config.get('Credentials', 'api_secret')

        try:
            lastfm = pylast.LastFMNetwork(api_key = api_key,
                                          api_secret = api_secret,
                                          username = username,
                                          password_hash = password_hash)
        except pylast.WSError as error:
            print("Failed to log in:", error)

    return lastfm



def get_lastfm_track_info( track_details, lastfm ):
    """Gets all necessary track details from lastfm

    Does overrides for mislabelled songs, and attempts translations
    for common ways of changing artist / track details

    Arguments:

    track_details -- dict containing keys for Artist and Title
    lastfm -- authenticated connection to the Last.FM API

    Returns None if failed
            Dict containing: Artist, Title, Album, MBID, LFID

    """

    # Four possible outcomes of track details:
    #
    # * artist or song is overridden, then looked up
    #   => store with valid artist, title, album, MBID, LFID
    # * track is looked up and is not in db
    #   => store with artist, title, album = NULL, MBID = NULL, LFID = NULL
    # * track is looked up, is in db, but does not have an album associated
    #   * try again with common translations
    #     * found album
    #       => store with valid artist, title, album, MBID, LFID
    #     * did not find album
    #       => store with artist, title, album = NULL, MBID = NULL, LFID
    #
    # * LFID = NULL means that a translation or override yaml entry
    #   needs to be created
    # * MBID = NULL means that an album is not set up for that track yet

    # Apply any artist / song overrides
    artist = whats_on_translate.override_artist(track_details['Artist'])
    song = whats_on_translate.override_song((track_details['Artist'],
                                             track_details['Title']))

    if artist is None:
        artist = track_details['Artist']

    if song is None:
        song = track_details['Title']

    track = get_lastfm_track( {'Artist': artist, 'Title': song}, lastfm )

    if track:
        album = get_lastfm_album( track )
        mbid = get_lastfm_mbid( track )
        track_id = get_lastfm_id( track )

        ret = {'Artist': artist, 'Title': song}

        if album:
            ret['Album'] = album
        if mbid:
            ret['MBID'] = mbid
        if track_id:
            ret['LFID'] = track_id

        return ret
    else:
        return None


def get_lastfm_track( track_details, lastfm ):
    """Gets a lastfm track

    Arguments:

    track_details -- dict containing keys for Artist and Title
    lastfm -- authenticated connection to the Last.FM API

    Returns a lastfm track object if successful, None if failed

    """
    track = None
    album = None

    # Find the track
    # If it's valid
    #   check if its album is valid
    # If the track is invalid or its album is invalid
    #   Translate it
    #   Search again
    #   If the album is not none
    #       Return this track
    #   Else
    #       Return the original track can be None or valid

    # Last.fm limits API calls to five per second from a specific IP
    time.sleep(0.2)

    try:
        track = lastfm.get_track(track_details['Artist'],
                                 track_details['Title'])
        if VERBOSE:
            print("Found track:", track)
    except pylast.WSError as error:
        print("Track not found:", error, track_details)

    if track is not None:
        album = get_lastfm_album( track )
        if VERBOSE:
            print("Valid track, checking for album:", album)
        orig_track = track

    if track is None or album is None:
        if VERBOSE:
            print("Invalid track or album, translating")

        artist = whats_on_translate.translate_artist(track_details['Artist'])
        song = whats_on_translate.translate_song((track_details['Artist'],
                                                    track_details['Title']))

        if artist != track_details['Artist'] or song != track_details['Title']:
            time.sleep(0.2)

            try:
                track = lastfm.get_track(artist, song)
                if VERBOSE:
                    print("Found translated track:", track, artist, song)
            except pylast.WSError as error:
                print("Track not found:", error, track_details)
            if track is not None:
                album = get_lastfm_album( track )
                if album is None:
                    if VERBOSE:
                        print("No album for", track, "using original", orig_track)
                    track = orig_track
        else:
            #if VERBOSE:
            if True:
                print("No translations for", track_details)

    return track

def get_lastfm_id( track ):
    track_id = None

    try:
        track_id = track.get_id()
    except pylast.MalformedResponseError as error:
        print("Malformed response", error)
    except pylast.WSError as error:
        if VERBOSE:
            print("LastFM ID not found:", error, track)

    return track_id

def get_lastfm_mbid( track ):
    mbid = None

    try:
        mbid = track.get_mbid()
    except pylast.MalformedResponseError as error:
        print("Malformed response", error)
    except pylast.WSError as error:
        if VERBOSE:
            print("MBID not found:", error, track)

    return mbid

def get_lastfm_artist( track ):
    artist = None

    try:
        artist = track.get_artist()
    except pylast.MalformedResponseError as error:
        print("Malformed response", error)
    except pylast.WSError as error:
        if VERBOSE:
            print("Artist not found:", error, track)

    return artist

def get_lastfm_album( track ):
    title = None

    try:
        album = track.get_album()
        if album is not None:
            title = album.get_title()
    except pylast.MalformedResponseError as error:
        print("Malformed response", error)
    except pylast.WSError as error:
        if VERBOSE:
            print("Album not found:", error, track)

    return title


if __name__ == "__main__":
    main()
