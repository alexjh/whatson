#!/usr/bin/python

"""Queries the databases for songs where the album string is '' and deletes
that attribute."""

from __future__ import print_function
import boto
import datetime
import yaml
import sys


def main():
    """Cleans up any entires that have an empty album string"""
    
    print(datetime.datetime.now())

    try:
        stations_yaml = open('stations.yaml')
    except IOError:
        print("Failed to load station list", file=sys.stderr)
        sys.exit(-1)

    stations = yaml.load(stations_yaml)

    sdb = boto.connect_sdb()

    for station_id in stations.keys():
        delete_empty_album_string( station_id, sdb )

    print(datetime.datetime.now())


def delete_empty_album_string( station, sdb ):
    """Clean up entries that have an empty (but not NULL) album string.

    Arguments:

    station -- Station ID string used to access the domain
    sdb     -- SimpleDB connection

    """

    domain = sdb.get_domain("%s-whatson" % station )

    query = 'select * from `%s` where Album = ""' % domain.name
    result_set = domain.select(query)
    for item in result_set:
        domain.delete_attributes(item.name, ['Album'], ['Album', ''])

if __name__ == "__main__":
    main()
