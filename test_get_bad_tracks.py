#!/usr/bin/python
"""Tests for the whats_on_get_bad_tracks file"""

import whats_on_get_bad_tracks

#------------------------------------------------------------------------

# Setup: 
#   - create a domain with two NULL LFID, two valid
#   - domain will be named with a timestamp
#        
# Test:
#   - check if it returns only the two null LFIDs
#
# Teardown: delete the domain
#   - delete the created db

def test_find_null_lfid():
    assert False
