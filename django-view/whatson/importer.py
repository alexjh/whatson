#!/usr/bin/python
"""Imports data from SimpleDB and generates a YAML file that can be
consumed by Django"""

import yaml
import urllib
import datetime
import tempfile
import subprocess
import os
import collections

BASE_URL = 'http://192.168.0.10:8000/api/v1/Airplay/?format=yaml'

STATION_URL = BASE_URL + '&order_by=-timestamp&station__id=%d&limit=1'

PK_URL = BASE_URL + '&order_by=-id&limit=1'

def import_from_original_db():
    """Imports the original data to acquire the primary keys"""
    if False:
        temp_file = tempfile.mkstemp(suffix='.yaml', prefix='whatson-')

        models = ['track', 'release', 'artist', 'station']

        for model in models:
            cmdline = "python manage.py dumpdata " \
                      "--format=yaml musiclog.%s >> %s" % (model, temp_file[1])
            subprocess.call(cmdline, shell=True)

        os.fsync(temp_file[0])
        import_data = os.fdopen(temp_file[0])
    else:
        import_data = open('track-data.yaml')

    import_yaml = yaml.safe_load(import_data)

    # It looks like Django dumpdata orders things by their pk, but
    # is this guaranteed? Perform an extra dict -> OrderedDict just
    # to be safe.

    # Generate the station dict
    station_list_comp = [(entry['fields']['callsign'], entry['pk']) \
                         for entry in import_yaml \
                         if entry['model'] == 'musiclog.station']
    tmp_station_dict = {key: value for (key, value) in station_list_comp}
    station_dict = collections.OrderedDict(
        sorted(tmp_station_dict.items(), key=lambda t: t[1]))

    # Generate the artist dict
    artist_list_comp = [(entry['fields']['name'], entry['pk']) \
                         for entry in import_yaml \
                         if entry['model'] == 'musiclog.artist']
    tmp_artist_dict = {key: value for (key, value) in artist_list_comp}
    artist_dict = collections.OrderedDict(
        sorted(tmp_artist_dict.items(), key=lambda t: t[1]))

    # Generate the release dict
    release_list_comp = [(entry['fields']['title'], entry['pk']) \
                         for entry in import_yaml \
                         if entry['model'] == 'musiclog.release']
    tmp_release_dict = {key: value for (key, value) in release_list_comp}
    release_dict = collections.OrderedDict(
        sorted(tmp_release_dict.items(), key=lambda t: t[1]))

    # Generate the track dict
    track_list_comp = [((entry['fields']['title'], entry['fields']['artist']),
                          entry['pk']) \
                        for entry in import_yaml \
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
    latest_airplay_pk_yaml = yaml.load(latest_airplay_pk_file)
    return latest_airplay_pk_yaml['objects'][0]['id']

def get_latest_station_airplay(station_pk):
    """Gets the latest airplay from a specific station

    Returns a timestamp for the airplay.
    """
    remote_file = urllib.urlopen(STATION_URL % station_pk)
    latest_yaml = yaml.load(remote_file)

    return datetime.datetime.strptime(
            latest_yaml['objects'][0]['timestamp'],
            "%Y-%m-%dT%H:%M:%S")

def main():
    """Generate YAML data to be consumed by Django"""

    (station_dict,
     artist_dict,
     release_dict,
     track_dict) = import_from_original_db()

    print "# ", station_dict

    new_artists = []
    new_releases = []
    new_tracks = []
    airplay_list = []

    latest_airplay_pk = get_latest_airplay_pk()

    for callsign, station_pk in station_dict.items():
        timestamp = get_latest_station_airplay(station_pk)
        epoch = int((timestamp - datetime.datetime(1970, 1, 1)).total_seconds())
        print "# ", epoch
        print "# ", callsign

        # TODO get the list of songs from SimpleDB that are newer than
        # the timestamp

        for airplay in airplay_list:
            artist_pk = None
            release_pk = None
            track_pk = None

            # Determine the artist_pk by generating it or finding it in the
            # dict.
            if airplay['Artist'] not in artist_dict:
                if len(artist_dict) != 0:
                    artist_pk = artist_dict[-1] + 1
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
            if airplay['Album'] is not None:
                if airplay['Album'] not in release_dict:
                    if len(release_dict) != 0:
                        release_pk = release_dict[-1] + 1
                    else:
                        release_pk = 1
                    new_releases.append(
                        {'fields': {'name': airplay['Album']},
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
                        track_pk = track_dict[-1] + 1
                    else:
                        track_pk = 1

                    if 'LFID' in airplay:
                        lfid = airplay['LFID']
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
            else:
                print "# Error adding track:", airplay

            # If the track_pk is None, something has gone wrong, so skip it
            if track_pk != None:
                latest_airplay_pk += 1
                airplay_list.append(
                        {
                          'fields': {
                            'track': track_pk,
                            'station': station_pk,
                            'timestamp': timestamp,
                          },
                          'model': 'musiclog.track',
                          'pk': latest_airplay_pk,
                        }

                    )
            else:
                print "# Failed to add airplay:", callsign, airplay

    print yaml.safe_dump(new_artists)
    print yaml.safe_dump(new_releases)
    print yaml.safe_dump(new_tracks)
    print yaml.safe_dump(airplay_list)


if __name__ == "__main__":
    main()
