#!/usr/bin/python
"""Tests for the whats_on_translate file"""

import whats_on_translate

#------------------------------------------------------------------------

OVERRIDE_ARTIST_EQ = [
                      ('Who', 'The Who'),
                     ]

OVERRIDE_ARTIST_NE = [
                      ('dude', 'fail'),
                     ]

def test_override_artist():
    """Tests the override_artist function"""
    for override in OVERRIDE_ARTIST_EQ:
        print("Checking", override[0])
        assert override[1] == whats_on_translate.override_artist(override[0])
    for override in OVERRIDE_ARTIST_NE:
        print("Checking", override[0])
        assert override[1] != whats_on_translate.override_artist(override[0])

#------------------------------------------------------------------------

OVERRIDE_SONG_EQ = [
                    (('deadmau5', "Ghosts 'N Stuff"), "Ghosts N Stuff"),
                   ]

OVERRIDE_SONG_NE = [
                    (('foo', "Ghosts 'N Stuff"), "Ghosts N Stuff"),
                    (('deadmau5', "'N Stuff"), "Ghosts N Stuff"),
                   ]

def test_override_song():
    """Tests the override_song function"""
    for override in OVERRIDE_SONG_EQ:
        assert override[1] == whats_on_translate.override_song(override[0])
    for override in OVERRIDE_SONG_NE:
        assert override[1] != whats_on_translate.override_song(override[0])
