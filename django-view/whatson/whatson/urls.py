from django.conf.urls import patterns, include, url

# Static files during deployment
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Tastypie
from tastypie.api import Api
from musiclog.api import TrackResource, ArtistResource, StationResource, ReleaseResource, AirplayResource

# HTML5 Boilerplate
from dh5bp.urls import urlpatterns as dh5bp_urls




# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# Tastypie
v1_api = Api(api_name='v1')

v1_api.register( TrackResource() )
v1_api.register( AirplayResource() )
v1_api.register( ReleaseResource() )
v1_api.register( StationResource() )
v1_api.register( ArtistResource() )

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'whatson.views.home', name='home'),
    # url(r'^whatson/', include('whatson.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    # Tastypie
    (r'^api/', include(v1_api.urls)),

    # Musiclog
    url(r'^musiclog/', include('musiclog.urls')),
)

# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += staticfiles_urlpatterns()
urlpatterns += dh5bp_urls
