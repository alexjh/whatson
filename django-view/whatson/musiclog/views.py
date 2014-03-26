# Create your views here.
"""Views for the musiclog app"""

from django.http import HttpResponse
from django.template import RequestContext, loader
from django.db.models import Count

from musiclog.models import Airplay, Artist, Track, Station

def gen_colour_list(length):
    """Return a list of colours of size 'length'"""
    colour = []
    colour_seed = 0xF7464A

    for _ in range(0, length):
        colour.append("#%06X" % colour_seed)
        colour_seed += 0xB46090
        colour_seed %= 0xFFFFFF

    return colour

def gen_graph_array(variable, graph_data):
    """Generates a javascript array to be used by the doughnut graph"""
    array_text = 'var %s = [\n' % variable

    for i in graph_data:
        array_text += ('  {\n')
        for k, value in i.iteritems():
            if k == 'color':
                array_text += '    ' + k + ": " + '"' + value + '",\n'
            else:
                array_text += '    ' + k + ": " + str(value) + ',\n'
        array_text += '  },\n'

    array_text += '];\n'

    return array_text

def gen_doughnut_data(value_dict, value_key, var_name):
    """Generates a doughnut graph javascript variable string
    to be used by the JS graphing library"""
    colour = gen_colour_list(len(value_dict))

    data = []
    for colour_idx, value in enumerate(value_dict):
        data.append({
            'color': colour[colour_idx],
            'value': value[value_key],
            })

    return gen_graph_array(var_name, data), colour


def index(request):
    """Main page of the musiclog app"""
    latest_airplays = Airplay.objects.all().order_by('-timestamp')[:10]
    template = loader.get_template('musiclog/index.html')
    context = RequestContext(request, {
                'latest_airplays': latest_airplays,
                    })
    return HttpResponse(template.render(context))


def airplay_all(request):
    """Airplay summary page of the musiclog app"""

    recent_songs = Airplay.objects.order_by('-timestamp')

    template = loader.get_template('musiclog/airplay_all.html')
    context = RequestContext(request, {
                'recent_songs': recent_songs[:20],
                    })
    return HttpResponse(template.render(context))


def track_all(request):
    """track summary page of the musiclog app"""

    recent_songs = Airplay.objects.order_by('-timestamp')

    template = loader.get_template('musiclog/track_all.html')
    context = RequestContext(request, {
                'recent_songs': recent_songs[:20],
                    })
    return HttpResponse(template.render(context))


def release_all(request):
    """release summary page of the musiclog app"""

    template = loader.get_template('musiclog/release_all.html')
    context = RequestContext(request, {
                    })
    return HttpResponse(template.render(context))


def artist_all(request):
    """artist summary page of the musiclog app"""

    recent_songs = Airplay.objects.order_by('-timestamp')
    template = loader.get_template('musiclog/artist_all.html')
    context = RequestContext(request, {
                'recent_songs': recent_songs[:20],
                    })
    return HttpResponse(template.render(context))


def station_all(request):
    """station summary page of the musiclog app"""

    stations = Station.objects.all().order_by('name')

    template = loader.get_template('musiclog/station_all.html')
    context = RequestContext(request, {
                'stations': stations,
                    })
    return HttpResponse(template.render(context))


def airplay(request):
    """Airplay page of the musiclog app"""
    template = loader.get_template('musiclog/airplay.html')
    context = RequestContext(request, {
                    })
    return HttpResponse(template.render(context))


def track(request, track_id=0):
    """Track page of the musiclog app"""

    track_info = Track.objects.get(pk=track_id)
    newest_play = Airplay.objects.filter(track__pk=track_id).\
                      order_by('-timestamp')
    first_play = Airplay.objects.filter(track__pk=track_id).\
                      order_by('timestamp')[0]

    # station_plays is the Airplays of the track, grouped by station
    # and ordered by station

    num_stations = 20
    station_plays = Airplay.objects.filter(track__pk=track_id) \
                        .values('station__name', 'station__id') \
                        .annotate(Count('station__id'))\
                        .order_by('-station__id__count')[:num_stations]

    # Get the absolute urls for the stations
    station_urls = []
    for station_query in station_plays:
        station_obj = Station.objects.get(pk=station_query['station__id'])
        station_urls.append(station_obj.get_absolute_url())


    # Generate the javascript variable used for the doughnut graph
    doughnut_data, colour = gen_doughnut_data(station_plays,
                                      'station__id__count',
                                      'station_doughnut')


    # Set up the Django template and context
    template = loader.get_template('musiclog/track.html')
    context = RequestContext(request, {
        'track_info':  track_info,
        'newest_play': newest_play[0],
        'first_play':  first_play,
        'track_plays':  newest_play[:10],
        'station_plays':  zip(station_plays,
            colour,
            station_urls,
            ),
        'station_doughnut': doughnut_data,
        })
    return HttpResponse(template.render(context))





def release(request):
    """Release page of the musiclog app"""
    template = loader.get_template('musiclog/release.html')
    context = RequestContext(request, {
                    })
    return HttpResponse(template.render(context))



def artist(request, artist_id=0):
    """Artist page of the musiclog app"""

    # List of all tracks belonging to this artist
    artist_tracks = Track.objects.filter(artist__pk=artist_id)

    latest_airplays = Airplay.objects.filter(track__in=artist_tracks) \
                         .order_by('-timestamp')[:10]

    airplay_counts = Airplay.objects.filter(track__in=artist_tracks)\
                        .values('track__title', 'track__id') \
                        .annotate(Count('track__id'))\
                        .order_by('-track__id__count')[:10]

    airplay_urls = []
    for airplay_query in airplay_counts:
        airplay_obj = Track.objects.get(pk=airplay_query['track__id'])
        airplay_urls.append(airplay_obj.get_absolute_url())

    doughnut_data, colour = gen_doughnut_data(airplay_counts,
            'track__id__count',
            'doughnut_data',
            )

    # Use tracks by artist to find Airplays by artist, grouped by station
    station_counts = Airplay.objects.filter(track__in=artist_tracks)\
                        .values('station__name', 'station__id') \
                        .annotate(Count('station__id'))\
                        .order_by('-station__id__count')[:20]

    station_urls = []
    for station_query in station_counts:
        station_obj = Station.objects.get(pk=station_query['station__id'])
        station_urls.append(station_obj.get_absolute_url())

    doughnut_data2, colour2 = gen_doughnut_data(station_counts,
            'station__id__count',
            'station_doughnut',
            )

    template = loader.get_template('musiclog/artist.html')
    context = RequestContext(request, {
        'latest_airplays': latest_airplays,
        'artist_tracks': artist_tracks,
        'artist_info': Artist.objects.get(pk=artist_id),
        'airplay_popular': zip(
            airplay_counts,
            colour,
            airplay_urls,
            ),
        'doughnut_data': doughnut_data,
        'station_plays': zip(
            station_counts,
            colour2,
            station_urls,
            ),
        'station_doughnut': doughnut_data2,
        })

    return HttpResponse(template.render(context))





def station(request, station_id=0):
    """Station page of the musiclog app"""

    station_info = Station.objects.get(pk=station_id)

    # List of all tracks belonging to this station
    recent_songs = Airplay.objects.filter(station__pk=station_id) \
                        .order_by('-timestamp')


    artists_num = 15
    popular_artists = Airplay.objects.filter(station__pk=station_id) \
                        .values('track__artist__id', 'track__artist__name') \
                        .annotate(Count('track__artist__id'))\
                        .order_by('-track__artist__id__count')[:artists_num]

    artist_urls = []
    for artist_query in popular_artists:
        artist_obj = Artist.objects.get(pk=artist_query['track__artist__id'])
        artist_urls.append(artist_obj.get_absolute_url())

    # Find Airplays by station, grouped by artist
    station_counts = Airplay.objects.filter(station__pk=station_id)\
                        .values('track__artist__name', 'track__artist__id') \
                        .annotate(Count('track__artist__id'))\
                        .order_by('-track__artist__id__count')[:artists_num]

    doughnut_data, colour = gen_doughnut_data(
            station_counts,
            'track__artist__id__count',
            'artists_doughnut',
            )

    template = loader.get_template('musiclog/station.html')
    context = RequestContext(request, {
        'station_info': station_info,
        'recent_songs': recent_songs[:10],
        'popular_artists': zip(
            popular_artists,
            colour,
            artist_urls,
            ),
        'artists_doughnut': doughnut_data,
        })
    return HttpResponse(template.render(context))

