# musiclog/api.py
import json
from tastypie.resources import ModelResource
from musiclog.models import Track, Artist, Release, Airplay, Station


class ArtistResource(ModelResource):
    class Meta:
        queryset = Artist.objects.all()
        resource_name = 'Artist'

class ReleaseResource(ModelResource):
    class Meta:
        queryset = Release.objects.all()
        resource_name = 'Release'

class StationResource(ModelResource):
    class Meta:
        queryset = Station.objects.all()
        resource_name = 'Station'

class AirplayResource(ModelResource):
    class Meta:
        queryset = Airplay.objects.all()
        resource_name = 'Airplay'

class TrackResource(ModelResource):
    class Meta:
        queryset = Track.objects.all()
        resource_name = 'Track'


