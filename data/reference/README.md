# Reference data

Small lookup tables that the project builds once and keeps, so the work can be
repeated without asking an outside service again. Unlike `data/raw/`, these
files are produced by this project and are committed to the repository.

## city_coordinates.csv

Latitude and longitude for each of the 22 cities that have a store.

- Produced by: `notebooks/02_gis_foundation.ipynb`, Step 2
- Source: OpenStreetMap, through the Nominatim geocoder (`geopy` package),
  asked for "city, state, Ecuador"
- Licence: map data © OpenStreetMap contributors, available under the Open
  Database Licence (ODbL). Credit must be kept with any published use.
- Columns: `state`, `city`, `stores`, `latitude`, `longitude`, `query_used`,
  `matched_address`
- Checks: every point is tested against a rough outline of mainland Ecuador
  and plotted on a map (Step 3) before it is trusted.
- To refresh: delete the file and rerun Step 2.
