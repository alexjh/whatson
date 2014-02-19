#!/usr/bin/python


# Translations:
#
# * TODO: YAML based
# * Artist: Remove anything past " feat " or " feat." or " w/" or " &"
# * Song: Remove parens
# * Song: Remove anything past "/"

EXAMPLE_ARTISTS = ['Jimmy Buffett W/Clint Black, Kenny Chesney, Alan Jackson, Toby Keith & Geor',
                   'Dude & Foo feat dude1',
                  ]

EXAMPLE_SONGS = []

def translate_artist( artist ):
    """Converts artist name into something that last.fm / Musicbrainz 
    understands

    Arguments:

    artist -- Artist name to be translated

    Returns the translated name"""

    artist_lower = artist.lower()
    print artist_lower

    shortest_pos = len(artist_lower)

    for suffix in [" feat ", 
                   " feat.", 
                   " w/", 
                   " &"]:
        pos = artist_lower.find(suffix)
        if pos > 0 and pos < shortest_pos:
            shortest_pos = pos

    return artist[0:shortest_pos]

def translate_song( song ):
    """Converts song title into something that last.fm / Musicbrainz 
    understands

    Arguments:

    song -- Song title to be translated

    Returns the translated name"""

    song_lower = song.lower()
    print song_lower

    shortest_pos = len(song_lower)

    for suffix in [" (",
                   "/"]:
        pos = song_lower.find(suffix)
        if pos > 0 and pos < shortest_pos:
            shortest_pos = pos

    return song[0:shortest_pos]


def main():
    for artist in EXAMPLE_ARTISTS:
        print translate_artist( artist )

    for song in EXAMPLE_SONGS:
        print translate_song( song )

if __name__ == '__main__':
    main()
