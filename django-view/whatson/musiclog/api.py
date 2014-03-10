# musiclog/api.py
import json
from tastypie import fields
from tastypie.authorization import DjangoAuthorization
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
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
        filtering = {
                       'id': ALL_WITH_RELATIONS,
                    }

class AirplayResource(ModelResource):
    station = fields.ForeignKey(StationResource,
                                'station',
                                blank=True,
                                null=True)

    class Meta:
        queryset = Airplay.objects.all()
        resource_name = 'Airplay'

        ordering = [
                     'timestamp',
                     'id',
                   ]
        filtering = {
                       'station': ALL_WITH_RELATIONS,
                    }

class TrackResource(ModelResource):
    class Meta:
        queryset = Track.objects.all()
        resource_name = 'Track'


