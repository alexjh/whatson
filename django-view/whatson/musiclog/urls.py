from django.conf.urls import patterns, url

from musiclog import views

urlpatterns = patterns('',
        url(r'^$', views.index, name='index'),

        # General view
        url(r'airplay/$', views.airplay_all, name='airplay_all'),
        url(r'track/$',   views.track_all,   name='track_all'),
        url(r'release/$', views.release_all, name='release_all'),
        url(r'artist/$',  views.artist_all,  name='artist_all'),
        url(r'station/$', views.station_all, name='station_all'),

        # Pages for specific items
        url(r'airplay/(?P<airplay_id>\d+)/$', views.airplay, name='airplay'),
        url(r'track/(?P<track_id>\d+)/$',     views.track,   name='track'),
        url(r'release/(?P<release_id>\d+)/$', views.release, name='release'),
        url(r'artist/(?P<artist_id>\d+)/$',   views.artist,  name='artist'),
        url(r'station/(?P<station_id>\d+)/$', views.station, name='station'),
        )
