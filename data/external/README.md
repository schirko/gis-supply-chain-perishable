# data/external

Third-party reference data that this project uses but does not own. The files are not committed (see `.gitignore`); download them again with the steps below.

## Natural Earth: Admin 1 – States, Provinces (1:10m)

| Item | Detail |
|---|---|
| Used for | Province boundaries of Ecuador (24 provinces), to check that each store city sits in the right province (notebook 02, Step 4) |
| Version | 5.1.1 |
| Licence | Public domain (see https://www.naturalearthdata.com/about/terms-of-use/) |
| Download | https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_1_states_provinces.zip |
| Where to put it | Unzip into `data/external/ne_10m_admin_1_states_provinces/` |
| Coordinate system | EPSG:4326 (longitude/latitude) |

### Known problem

In version 5.1.1 the names of **Napo** and **Tungurahua** are swapped. Napo should be about 12,500 km² and Tungurahua about 3,300 km², but the file has them the other way round (both rows carry `check_me` = 12). Notebook 02 detects this from the areas and swaps the names back. If you use the file elsewhere, check it yourself.
