"""Admin view of musiclog"""

from django.contrib import admin
from musiclog.models import Artist, Release, Track, Station, Airplay

admin.site.register(Artist)
admin.site.register(Release)
admin.site.register(Track)
admin.site.register(Station)
admin.site.register(Airplay)
