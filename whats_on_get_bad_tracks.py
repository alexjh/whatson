#!/usr/bin/python
# vim: set fileencoding=utf-8 :

"""Queries the databases for songs where the LFID is NULL

This indicates a track that wasn't found in last.fm."""

from __future__ import print_function
import boto
import datetime
import yaml
import sys


def main():
    """Finds any entries that have a NULL LFID"""
    
    print(datetime.datetime.now())

    try:
        stations_yaml = open('stations.yaml')
    except IOError:
        print("Failed to load station list", file=sys.stderr)
        sys.exit(-1)

    stations = yaml.load(stations_yaml)

    sdb = boto.connect_sdb()

    null_lfid = []

    for station_id in stations.keys():
        find_null_lfid( station_id, sdb, null_lfid )

    results = yaml.safe_dump(sorted(null_lfid), default_flow_style=False)

    print(results)

    print(datetime.datetime.now())


def find_null_lfid( station, sdb, null_lfid ):
    """Appends any NULL LFIDs albums to the list"""

    try:
        domain = sdb.get_domain("%s-whatson" % station )
    except boto.exception.SDBResponseError:
        return

    query = 'select * from `%s` where `LFID` is NULL' % domain.name
    result_set = domain.select(query)
    for item in result_set:
        null_track = {item['Artist']: item['Title']}
        if null_track not in null_lfid:
            null_lfid.append(null_track)

if __name__ == "__main__":
    main()
