#!/usr/bin/python
"""Imports data from SimpleDB and generates a JSON file that can be
consumed by Django"""

import json
import urllib
import datetime
import tempfile
import subprocess
import os
import collections
import boto
import pytz
import dateutil.parser

BASE_URL = 'http://192.168.0.10:8000/api/v1/Airplay/?format=json'

STATION_URL = BASE_URL + '&order_by=-timestamp&station__id=%d&limit=1'

PK_URL = BASE_URL + '&order_by=-id&limit=1'

def import_from_original_db():
    """Imports the original data to acquire the primary keys"""
    if False:
        temp_file = tempfile.mkstemp(suffix='.json', prefix='whatson-')

        models = ['track', 'release', 'artist', 'station']

        for model in models:
            cmdline = "python manage.py dumpdata " \
                      "--format=json musiclog.%s >> %s" % (model, temp_file[1])
            subprocess.call(cmdline, shell=True)

        os.fsync(temp_file[0])
        import_data = os.fdopen(temp_file[0])
    else:
        import_data = open('track-data.json')

    import_json = json.load(import_data)

    # It looks like Django dumpdata orders things by their pk, but
    # is this guaranteed? Perform an extra dict -> OrderedDict just
    # to be safe.

    # Generate the station dict
    station_list_comp = [(entry['fields']['callsign'], (entry['pk'], entry['fields']['timezone'])) \
                         for entry in import_json \
                         if entry['model'] == 'musiclog.station']
    tmp_station_dict = {key: value for (key, value) in station_list_comp}
    station_dict = collections.OrderedDict(
        sorted(tmp_station_dict.items(), key=lambda t: t[1]))

    # Generate the artist dict
    artist_list_comp = [(entry['fields']['name'], entry['pk']) \
                         for entry in import_json \
                         if entry['model'] == 'musiclog.artist']
    tmp_artist_dict = {key: value for (key, value) in artist_list_comp}
    artist_dict = collections.OrderedDict(
        sorted(tmp_artist_dict.items(), key=lambda t: t[1]))

    # Generate the release dict
    release_list_comp = [(entry['fields']['title'], entry['pk']) \
                         for entry in import_json \
                         if entry['model'] == 'musiclog.release']
    tmp_release_dict = {key: value for (key, value) in release_list_comp}
    release_dict = collections.OrderedDict(
        sorted(tmp_release_dict.items(), key=lambda t: t[1]))

    # Generate the track dict
    track_list_comp = [((entry['fields']['title'], entry['fields']['artist']),
                          entry['pk']) \
                        for entry in import_json \
                        if entry['model'] == 'musiclog.track']
    tmp_track_dict = {key: value for (key, value) in track_list_comp}
    track_dict = collections.OrderedDict(
        sorted(tmp_track_dict.items(), key=lambda t: t[1]))

    return (station_dict, artist_dict, release_dict, track_dict)

def get_latest_airplay_pk():
    """Queries the web API for the latest airplay PK

    This is more efficient than parsing all of the airplay data

    Returns the latest airplay PK from all of the stations as
    an integer"""
    latest_airplay_pk_file = urllib.urlopen(PK_URL)
    latest_airplay_pk_json = json.load(latest_airplay_pk_file)
    if len(latest_airplay_pk_json['objects']):
        return latest_airplay_pk_json['objects'][0]['id']
    else:
        return 0

def get_latest_station_airplay(station_pk, station_tz):
    """Gets the latest airplay from a specific station

    Returns a timestamp for the airplay.
    """

    station_tz_type = pytz.timezone(station_tz)
    remote_file = urllib.urlopen(STATION_URL % station_pk)
    latest_json = json.load(remote_file)

    print latest_json

    if len(latest_json['objects']):
        ts = dateutil.parser.parse(latest_json['objects'][0]['timestamp'])
        print ts
        ts = pytz.UTC.localize(ts)
        print ts
        return ts.astimezone(station_tz_type)
    else:
        then = datetime.datetime(1970, 1, 1)
        then = pytz.UTC.localize(then)
        return then.astimezone(station_tz_type)

def get_recent_airplays( epoch, callsign ):
    """Queries SimpleDB for any airplays newer than epoch

    Returns list of dicts containing airplay details"""
    airplay_list = []

    sdb = boto.connect_sdb()

    try:
        domain = sdb.get_domain("%s-whatson" % callsign )
    except boto.exception.SDBResponseError:
        return []

    query = 'select * from `%s` where itemName() > "%08x" order by itemName() asc' % (domain.name, epoch)
    result_set = domain.select(query, max_items = 10)
    for item in result_set:
        airplay_list.append(
                (datetime.datetime.utcfromtimestamp(int(item.name, 16)),
                 item))

    return airplay_list

def main():
    """Generate JSON data to be consumed by Django"""

    (station_dict,
     artist_dict,
     release_dict,
     track_dict) = import_from_original_db()

    new_artists = []
    new_releases = []
    new_tracks = []
    new_airplay = []

    latest_airplay_pk = get_latest_airplay_pk()

    for callsign, (station_pk, station_tz) in station_dict.items():
        if callsign != 'CKGE':
            continue

        station_tz_type = pytz.timezone(station_tz)

        epoch_reference = datetime.datetime(1970, 1, 1)
        epoch_reference = pytz.UTC.localize(epoch_reference)
        epoch_reference = epoch_reference.astimezone(station_tz_type)

        timestamp = get_latest_station_airplay(station_pk, station_tz)
        print timestamp

        epoch = int((timestamp - epoch_reference).total_seconds())
        print epoch
        # get the list of songs from SimpleDB that are newer than
        # the timestamp
        airplay_list = get_recent_airplays( epoch, callsign )

        for (play_time, airplay) in airplay_list:
            print play_time

            artist_pk = None
            release_pk = None
            track_pk = None

            # Determine the artist_pk by generating it or finding it in the
            # dict.
            if airplay['Artist'] not in artist_dict:
                if len(artist_dict) != 0:
                    key = next(reversed(artist_dict))
                    artist_pk = artist_dict[key] + 1
                else:
                    artist_pk = 1
                new_artists.append(
                    {'fields': {'name': airplay['Artist']},
                     'model': 'musiclog.artist',
                     'pk': artist_pk}
                    )
                artist_dict[ airplay['Artist'] ] = artist_pk
            else:
                artist_pk = artist_dict[airplay['Artist']]

            # Determine the release pk
            if 'Album' in airplay:
                if airplay['Album'] not in release_dict:
                    if len(release_dict) != 0:
                        key = next(reversed(release_dict))
                        release_pk = release_dict[key] + 1
                    else:
                        release_pk = 1
                    new_releases.append(
                        {'fields': {'title': airplay['Album']},
                        'model': 'musiclog.release',
                        'pk': release_pk}
                        )
                    release_dict[ airplay['Album'] ] = release_pk
                else:
                    release_pk = release_dict[airplay['Album']]

            # If the artist_pk is not set up, something has gone wrong,
            # so don't add it to the list.
            #
            # However, an empty release_pk is valid.
            if artist_pk != None:

                # Add a new track_pk or find it in the dict
                if (airplay['Title'], artist_pk) not in track_dict:
                    if len(track_dict) != 0:
                        key = next(reversed(track_dict))
                        track_pk = track_dict[key] + 1
                    else:
                        track_pk = 1

                    if 'LFID' in airplay:
                        lfid = int(airplay['LFID'])
                    else:
                        lfid = None

                    if 'MBID' in airplay:
                        mbid = airplay['MBID']
                    else:
                        mbid = None

                    # Release, LFID, MBID can be None, but
                    # title and artist must be valid
                    new_tracks.append(
                      {'fields': {
                          'title': airplay['Title'],
                          'album': release_pk,
                          'artist': artist_pk,
                          'lfid': lfid,
                          'mbid': mbid,
                        },
                      'model': 'musiclog.track',
                      'pk': track_pk}
                      )
                    track_dict[ (airplay['Title'], artist_pk) ] = track_pk
                else:
                    track_pk = track_dict[(airplay['Title'], artist_pk)]

            # If the track_pk is None, something has gone wrong, so skip it
            if track_pk != None:
                latest_airplay_pk += 1
                play_time = pytz.UTC.localize(play_time)
                play_time = play_time.astimezone(station_tz_type)
                new_airplay.append(
                        {
                          'fields': {
                            'track': track_pk,
                            'station': station_pk,
                            'timestamp': play_time.isoformat(),
                          },
                          'model': 'musiclog.airplay',
                          'pk': latest_airplay_pk,
                        }

                    )

    if len(new_artists):
        print json.dumps(new_artists, indent=4, separators=(',', ': '))
    if len(new_releases):
        print json.dumps(new_releases, indent=4, separators=(',', ': '))
    if len(new_tracks):
        print json.dumps(new_tracks, indent=4, separators=(',', ': '))
    if len(new_airplay):
        print json.dumps(new_airplay, indent=4, separators=(',', ': '))


if __name__ == "__main__":
    main()
