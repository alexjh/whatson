# Create your views here.
"""Views for the musiclog app"""

from django.http import HttpResponse
from django.template import RequestContext, loader
from django.db.models import Count

from musiclog.models import Airplay, Artist, Track, Release, Station

def gen_colour_list( length ):
    colour = []
    colour_seed = 0xF7464A

    for i in range(0,length):
        colour.append( "#%06X" % colour_seed)
        colour_seed += 0xB46090
        colour_seed %= 0xFFFFFF

    return colour

def index(request):
    """Main page of the musiclog app"""
    latest_airplays = Airplay.objects.all().order_by('-timestamp')[:10]
    template = loader.get_template('musiclog/index.html')
    context = RequestContext(request, {
                'latest_airplays': latest_airplays,
                    })
    return HttpResponse(template.render(context))




def airplay(request, airplay_id = 0):
    """Airplay page of the musiclog app"""
    template = loader.get_template('musiclog/airplay.html')
    context = RequestContext(request, {
                    })
    return HttpResponse(template.render(context))




def track(request, track_id = 0):
    """Track page of the musiclog app"""

    track_info = Track.objects.get(pk=track_id)
    newest_play = Airplay.objects.filter( track__pk = track_id ).\
                      order_by('-timestamp')
    first_play = Airplay.objects.filter( track__pk = track_id ).\
                      order_by('timestamp')[0]

    # station_plays is the Airplays of the track, grouped by station
    # and ordered by station
    station_plays = Airplay.objects.filter( track__pk = track_id ) \
                        .values( 'station__name', 'station__id') \
                        .annotate(Count('station__id'))\
                        .order_by('-station__id__count')


    data = []

    colour = gen_colour_list( len(station_plays) )

    for index, station in enumerate(station_plays):
        temp_dict = {}
        temp_dict['color'] = colour[index]
        temp_dict['value'] = station['station__id__count']
        data.append(temp_dict)

    station_doughnut = "var station_doughnut = "
    station_doughnut += '[\n'

    for i in data:
        station_doughnut += ('  {\n')
        for k,v in i.iteritems():
            if k == 'color':
                station_doughnut += '    ' + k + ": " + '"' + v + '",\n'
            else:
                station_doughnut += '    ' + k + ": " + str(v) + ',\n'
        station_doughnut += '  },\n'


    station_doughnut += '];\n'

    template = loader.get_template('musiclog/track.html')
    context = RequestContext(request, {
                'track_info':  track_info,
                'newest_play': newest_play[0],
                'first_play':  first_play,
                'track_plays':  newest_play[:10],
                'station_plays':  zip(station_plays[:20], colour),
                'station_doughnut': station_doughnut,
                'table_colour': colour,
                    })
    return HttpResponse(template.render(context))





def release(request, release_id = 0):
    """Release page of the musiclog app"""
    template = loader.get_template('musiclog/release.html')
    context = RequestContext(request, {
                    })
    return HttpResponse(template.render(context))


# JSON views for:
#
# Artist view:
#
# * airplay counts by artist
# * artist counts by station

def artist(request, artist_id = 0):
    """Artist page of the musiclog app"""

    # Variables for template:
    artist_info = Artist.objects.get(pk=artist_id)

    # List of all tracks belonging to this artist
    artist_tracks = Track.objects.filter( artist__pk = artist_id )

    latest_airplays = Airplay.objects.filter( track__in = artist_tracks ) \
                         .order_by('-timestamp')[:10]

    airplay_counts = Airplay.objects.filter( track__in = artist_tracks )\
                        .values( 'track__title', 'track__id') \
                        .annotate(Count('track__id'))\
                        .order_by('-track__id__count')


    # TODO Generate a colour list of len(airplay_counts)
    # TODO Generate the graph data via helper function
    # TODO Display a legend with an icon for the colour to track mapping

    data = []
    colour = gen_colour_list( len(airplay_counts) )
    for index, airplay in enumerate(airplay_counts):
        temp_dict = {}
        temp_dict['color'] = colour[index]
        temp_dict['value'] = airplay['track__id__count']
        data.append(temp_dict)

    doughnut_data = "var doughnut_data = "
    doughnut_data += '[\n'

    for i in data:
        doughnut_data += ('  {\n')
        for k,v in i.iteritems():
            if k == 'color':
                doughnut_data += '    ' + k + ": " + '"' + v + '",\n'
            else:
                doughnut_data += '    ' + k + ": " + str(v) + ',\n'
        doughnut_data += '  },\n'


    doughnut_data += '];\n'


    # TODO station_doughnut
    #
    # Use tracks by artist to find Airplays by artist, grouped by station
    station_counts = Airplay.objects.filter( track__in = artist_tracks )\
                        .values( 'station__name', 'station__id') \
                        .annotate(Count('station__id'))\
                        .order_by('-station__id__count')

    data = []
    colour = gen_colour_list( len(station_counts) )

    for index, station in enumerate(station_counts):
        temp_dict = {}
        temp_dict['color'] = colour[index]
        temp_dict['value'] = station['station__id__count']
        data.append(temp_dict)

    station_doughnut = "var station_doughnut = "
    station_doughnut += '[\n'

    # TODO FIXME Move this to a function
    for i in data:
        station_doughnut += ('  {\n')
        for k,v in i.iteritems():
            if k == 'color':
                station_doughnut += '    ' + k + ": " + '"' + v + '",\n'
            else:
                station_doughnut += '    ' + k + ": " + str(v) + ',\n'
        station_doughnut += '  },\n'


    station_doughnut += '];\n'

    # Template File
    template = loader.get_template('musiclog/artist.html')

    # Mapping of variables to template variables
    context = RequestContext(request, {
                'latest_airplays': latest_airplays,
                'artist_tracks': artist_tracks,
                'artist_info': artist_info,
                'airplay_popular': zip(airplay_counts[:10], colour),
                'doughnut_data': doughnut_data,
                'station_plays': zip(station_counts[:20], colour),
                'station_doughnut': station_doughnut,
                    })

    return HttpResponse(template.render(context))








def station(request, station_id = 0):
    """Station page of the musiclog app"""

    station_info = Station.objects.get(pk=station_id)

    # List of all tracks belonging to this station
    recent_songs = Airplay.objects.filter( station__pk = station_id ) \
                        .order_by('-timestamp')
    
    popular_artists = Airplay.objects.filter( station__pk = station_id ) \
                        .values( 'track__artist__id', 'track__artist__name') \
                        .annotate(Count('track__artist__id'))\
                        .order_by('-track__artist__id__count')

    artists_num = 15

    # station_doughnut
    #
    # Find Airplays by station, grouped by artist
    station_counts = Airplay.objects.filter( station__pk = station_id )\
                        .values( 'track__artist__name', 'track__artist__id') \
                        .annotate(Count('track__artist__id'))\
                        .order_by('-track__artist__id__count')[:artists_num]

    data = []
    colour = gen_colour_list( len(station_counts) )

    for index, artist in enumerate(station_counts):
        temp_dict = {}
        temp_dict['color'] = colour[index]
        temp_dict['value'] = artist['track__artist__id__count']
        data.append(temp_dict)

    artists_doughnut = "var artists_doughnut = "
    artists_doughnut += '[\n'

    for i in data:
        artists_doughnut += ('  {\n')
        for k,v in i.iteritems():
            if k == 'color':
                artists_doughnut += '    ' + k + ": " + '"' + v + '",\n'
            else:
                artists_doughnut += '    ' + k + ": " + str(v) + ',\n'
        artists_doughnut += '  },\n'


    artists_doughnut += '];\n'

    template = loader.get_template('musiclog/station.html')
    context = RequestContext(request, {
                'station_info': station_info,
                'recent_songs': recent_songs[:10],
                'popular_artists': zip(popular_artists[:artists_num], colour),
                'artists_doughnut': artists_doughnut,
                    })
    return HttpResponse(template.render(context))

