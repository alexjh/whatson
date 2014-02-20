#!/usr/bin/python


from __future__ import print_function
import yaml

VERBOSE = False

# Translations:
#
# * YAML based takes precedence
# * Artist: Remove anything past " feat " or " feat." or " w/" or " &"
# * Song: Remove parens
# * Song: Remove anything past "/"

EXAMPLE_ARTISTS = ['Jimmy Buffett W/Clint Black, Kenny Chesney, Alan Jackson, Toby Keith & Geor',
                   'Dude & Foo feat dude1',
                   'Guess Who',
                  ]

EXAMPLE_SONGS = [('Trews', 'Power Of Positive Drinking'),
                 ('Prince', '- 1999 -'),
                 ('Trooper', 'The Boys In The Bright White Sports Cars')]

TRANSLATIONS = {}

def load_yaml():
    try:
        translations_yaml = open('translations.yaml')
        translations = yaml.load(translations_yaml)
    except IOError:
        translations = {}

    return translations

def override_artist( artist ):
    """Overrides the artist name

    Arguments:

    artist -- string containing name

    """

    if artist in TRANSLATIONS['artists'].keys():
        if VERBOSE:
            print("Translating", artist, "to", TRANSLATIONS['artists'][artist])
        return TRANSLATIONS['artists'][artist]
    return None

def translate_artist( artist ):
    """Converts artist name into something that last.fm / Musicbrainz 
    understands

    Arguments:

    artist -- Artist name to be translated

    Returns the translated name"""


    artist_lower = artist.lower()

    shortest_pos = len(artist_lower)

    for suffix in [" feat ", 
                   " feat.", 
                   " w/", 
                   " &"]:
        pos = artist_lower.find(suffix)
        if pos > 0 and pos < shortest_pos:
            shortest_pos = pos

    return artist[0:shortest_pos]

def override_song( song ):
    """Overrides the song title from YAML config

    Arguments:

    song -- tuple of (artist, song)

    Returns new song title or None
    
    """

    artist = translate_artist(song[0])

    if artist in TRANSLATIONS['songs'].keys():
        if song[1] in TRANSLATIONS['songs'][artist].keys():
            return str(TRANSLATIONS['songs'][artist][song[1]])
    return None

def translate_song( song ):
    """Converts artist and song title into something that last.fm / Musicbrainz 
    understands

    Arguments:

    song -- Song title to be translated

    Returns the translated name"""


    song_lower = song[1].lower()

    shortest_pos = len(song_lower)

    for suffix in [" (",
                   "/"]:
        pos = song_lower.find(suffix)
        if pos > 0 and pos < shortest_pos:
            shortest_pos = pos

    return song[1][0:shortest_pos]


def main():
    for artist in EXAMPLE_ARTISTS:
        artist_or = override_artist( artist )
        if artist_or:
            print(artist_or)
        else:
            print(translate_artist( artist ))

    for song in EXAMPLE_SONGS:
        song_or = override_song( song )
        if song_or:
            print(song_or)
        else:
            print(translate_song( song ))

TRANSLATIONS = load_yaml()

if __name__ == '__main__':
    main()
