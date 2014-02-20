# whatson

Radio Station scraping experiments

## Database layout:

key: epoch timestamp in %08x format to allow for sorting
values:
- Artist
- Title
- Album (optional)
- MBID (optional Musicbrainz ID, most likely artist or track name needs translation)
- LFID (optional LatFM ID, most likely artist or track name needs translation)

