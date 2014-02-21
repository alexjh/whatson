from django.conf.urls import patterns, url

from musiclog import views

urlpatterns = patterns('',
        url(r'^$', views.index, name='index'),
        url(r'artist/$', views.artist, name='artist')
        )
