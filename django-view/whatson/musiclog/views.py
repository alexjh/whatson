# Create your views here.
"""Views for the musiclog app"""

from django.http import HttpResponse
from django.template import RequestContext, loader
from django.db.models import Count

from musiclog.models import Airplay, Artist, Track, Release, Station

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
                      order_by('-timestamp')[0]
    first_play = Airplay.objects.filter( track__pk = track_id ).\
                      order_by('timestamp')[0]

    template = loader.get_template('musiclog/track.html')
    context = RequestContext(request, {
                'track_info':  track_info,
                'newest_play': newest_play,
                'first_play':  first_play,
                    })
    return HttpResponse(template.render(context))

def release(request, release_id = 0):
    """Release page of the musiclog app"""
    template = loader.get_template('musiclog/release.html')
    context = RequestContext(request, {
                    })
    return HttpResponse(template.render(context))





def artist(request, artist_id = 0):
    """Artist page of the musiclog app"""

    # Variables for template:
    artist_info = Artist.objects.get(pk=artist_id)

    # List of all tracks belonging to this artist
    artist_tracks = Track.objects.filter( artist__pk = artist_id )

    latest_airplays = Airplay.objects.filter( track__in = artist_tracks ) \
                         .order_by('-timestamp')[:10]

    # TODO Generate a doughnutData for the graph
    airplay_counts = Airplay.objects.filter( track__in = artist_tracks )\
                        .values( 'track__title', 'track__id') \
                        .annotate(Count('track__id'))\
                        .order_by('-track__id__count')


    # Template File
    template = loader.get_template('musiclog/artist.html')

    # Mapping of variables to template variables
    context = RequestContext(request, {
                'latest_airplays': latest_airplays,
                'artist_tracks': artist_tracks,
                'artist_info': artist_info,
                'airplay_counts': airplay_counts,
                    })
    return HttpResponse(template.render(context))








def station(request, station_id = 0):
    """Station page of the musiclog app"""
    template = loader.get_template('musiclog/station.html')
    context = RequestContext(request, {
                    })
    return HttpResponse(template.render(context))

