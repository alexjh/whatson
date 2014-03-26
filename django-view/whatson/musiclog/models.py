"""What's On Django Models"""

from django.db import models
import django.core.urlresolvers

class Artist(models.Model):
    """Represents an artist"""
    name = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        """Returns the absolute URL to be used by the template"""
        return django.core.urlresolvers.reverse('artist', args=[str(self.id)])

class Release(models.Model):
    """Represents an album"""
    title = models.CharField(max_length=200)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        """Returns the absolute URL to be used by the template"""
        return django.core.urlresolvers.reverse('release', args=[str(self.id)])

class Track(models.Model):
    """Represents a track associated with an album"""
    title = models.CharField(max_length=100)
    album = models.ForeignKey(Release, null=True, blank=True)
    artist = models.ForeignKey(Artist)
    lfid = models.PositiveIntegerField(null=True, blank=True)
    mbid = models.CharField(max_length=36, null=True, blank=True)

    class Meta:
        unique_together = ('title', 'album', 'artist')

    def __unicode__(self):
        if self.album:
            return "%s (%s)" % (self.title, self.album.title)
        else:
            return self.title

    def get_absolute_url(self):
        """Returns the absolute URL to be used by the template"""
        return django.core.urlresolvers.reverse('track', args=[str(self.id)])

class Station(models.Model):
    """Represents a station that plays tracks"""
    name = models.CharField(max_length=100)
    callsign = models.CharField(max_length=20, unique=True)
    timezone = models.CharField(max_length=50)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.callsign)

    def get_absolute_url(self):
        """Returns the absolute URL to be used by the template"""
        return django.core.urlresolvers.reverse('station', args=[str(self.id)])

class Airplay(models.Model):
    """Represents a played song"""
    timestamp = models.DateTimeField()
    track = models.ForeignKey(Track)
    station = models.ForeignKey(Station)

    class Meta:
        unique_together = ('station', 'timestamp')

    def __unicode__(self):
        return "%s @ %s" % (self.track.title, str(self.timestamp))

    def get_absolute_url(self):
        """Returns the absolute URL to be used by the template"""
        return django.core.urlresolvers.reverse('airplay', args=[str(self.id)])

