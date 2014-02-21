# Create your views here.

from django.http import HttpResponse

def index(request):
    return HttpResponse("Hello, world. You're at the musiclog index.")

def airplay(request, airplay_id = 0):
    return HttpResponse("Hello, world. You're at the airplay %d index." % airplay_id)

def track(request, track_id = 0):
    return HttpResponse("Hello, world. You're at the track %d index." % track_id)

def release(request, release_id = 0):
    return HttpResponse("Hello, world. You're at the release %d index." % release_id)

def artist(request, artist_id = 0):
    return HttpResponse("Hello, world. You're at the artist %d index." % artist_id)

def station(request, station_id = 0):
    return HttpResponse("Hello, world. You're at the station %d index." % station_id)

