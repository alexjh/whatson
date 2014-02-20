#!/usr/bin/python
"""Tests for the lastfm_utils module"""

import lastfm_utils

#------------------------------------------------------------------------

def test_get_lastfm_conn():
    assert lastfm_utils.get_lastfm_conn() != None
    assert lastfm_utils.get_lastfm_conn('/dev/null') == None

