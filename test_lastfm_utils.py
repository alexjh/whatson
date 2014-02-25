#!/usr/bin/python
"""Tests for the lastfm_utils module"""

import lastfm_utils

#------------------------------------------------------------------------

def test_get_lastfm_conn():
    """Tests the get_lastfm_conn function"""
    assert lastfm_utils.get_lastfm_conn() != None
    assert lastfm_utils.get_lastfm_conn('/dev/null') == None

def test_get_lastfm_track_info():
    """Tests the get_lastfm_track_info function"""
    assert False

def test_get_lastfm_track():
    """Tests the get_lastfm_track function"""
    assert False

def test_get_lastfm_id():
    """Tests the get_lastfm_id function"""
    assert False

def test_get_lastfm_mbid():
    """Tests the get_lastfm_mbid function"""
    assert False

def test_get_lastfm_album():
    """Tests the get_lastfm_album function"""
    assert False

def test_get_lastfm_artist():
    """Tests the get_lastfm_artist function"""
    assert False


