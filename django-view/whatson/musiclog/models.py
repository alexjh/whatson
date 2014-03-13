"""What's On Django Models"""

from django.db import models

class Artist(models.Model):
    """Represents an artist"""
    name = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return self.name

class Release(models.Model):
    """Represents an album"""
    title = models.CharField(max_length=200)

    def __unicode__(self):
        return self.title

class Track(models.Model):
    """Represents a track associated with an album"""
    title  = models.CharField(max_length=100)
    album  = models.ForeignKey( Release, null = True, blank = True )
    artist = models.ForeignKey( Artist )
    lfid   = models.PositiveIntegerField( null = True, blank = True )
    mbid   = models.CharField( max_length=36, null = True, blank = True )

    class Meta:
        unique_together = ('title', 'album', 'artist')

    def __unicode__(self):
        if self.album:
            return "%s (%s)" % (self.title, self.album.title)
        else:
            return self.title

class Station(models.Model):
    """Represents a station that plays tracks"""
    name = models.CharField(max_length=100)
    callsign = models.CharField(max_length=20, unique=True)
    timezone = models.CharField(max_length=50)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.callsign)

class Airplay(models.Model):
    """Represents a played song"""
    timestamp = models.DateTimeField()
    track = models.ForeignKey( Track )
    station = models.ForeignKey( Station )

    class Meta:
        unique_together = ('station', 'timestamp')

    def __unicode__(self):
        return "%s @ %s" % (self.track.title, str(self.timestamp))

