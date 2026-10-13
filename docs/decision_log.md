# Decision log

What was chosen, what was rejected, and why. Newest entries at the bottom. Each entry also says where the evidence is.

## 1. Dataset: Kaggle "Store Sales - Time Series Forecasting" (Corporación Favorita, Ecuador)
- **Chosen:** it has daily sales by store and product family, store cities and states, holidays and oil prices, and the geography is real (Ecuador).
- **Limits:** sales are per product family, not per item, and sales are not true demand (a stockout hides demand).
- **Evidence:** `notebooks/01_data_audit.ipynb`.

## 2. We do not use the contest files
- **Chosen:** hold out the last weeks of `train.csv` as our own test set. `test.csv` and `sample_submission.csv` are not used.
- **Why:** this is a learning and portfolio project, not a contest entry, and it keeps the project separate from any contest.

## 3. Perishable families
- **Chosen:** PRODUCE, DAIRY, MEATS, POULTRY, SEAFOOD, EGGS, BREAD/BAKERY, DELI, PREPARED FOODS.
- **Open:** the single family for the first app is chosen in notebook 03, after checking the share of zero-sales days.

## 4. City coordinates from OpenStreetMap (Nominatim)
- **Chosen:** look up each of the 22 store cities, then check every point on a map.
- **Found and fixed:** Libertad matched a Guayaquil neighbourhood. La Libertad is in Santa Elena (since 2007), though the sales file lists Guayas. Corrected by hand and checked to be near Salinas.
- **Evidence:** `notebooks/02_gis_foundation.ipynb` Steps 2 and 3; `data/reference/city_coordinates.csv`.

## 5. Province boundaries from Natural Earth (Admin 1, 1:10m, v5.1.1)
- **Chosen:** public domain, 24 Ecuador provinces, downloaded by hand into `data/external/` (not committed).
- **Found and fixed:** the names of Napo and Tungurahua are swapped in this version. The code compares areas and swaps them back.
- **Check:** every city must fall in the province the sales file gives (5 km tolerance for the coastline). Ibarra failed (the geocoder returned an area centre in Carchi) and was re-looked up as a city, which put it in Imbabura.
- **Limit:** accuracy is checked to province level only. A point can still be 10 to 15 km off inside the right province (Manta is the likeliest).
- **Evidence:** `notebooks/02_gis_foundation.ipynb` Step 4.

## 6. Assumed warehouse sites: Quito, Guayaquil, Cuenca, Santo Domingo
- **Method:** assign each city to its nearest candidate by straight-line distance (UTM metres) and score each setup by store-weighted average distance and longest distance.
- **Compared:** A (Quito, Guayaquil, Cuenca): average 49.4 km, longest 182.6 km. B (A plus Santo Domingo): 42.6 km, 164.6 km. C (A plus Manta): 43.3 km, 182.6 km, and Manta serves only 2 stores.
- **Chosen:** B. It is the shortest on both measures and splits the stores more evenly (Quito 25, Guayaquil 16, Cuenca 7, Santo Domingo 6).
- **Limits:** the sites are assumed, not the chain's real warehouses. Candidates came from judgment, so a better setup may exist. Distance is straight-line, not by road. Every store counts equally.
- **Evidence:** `notebooks/02_gis_foundation.ipynb` Step 5; `data/reference/warehouse_sites.csv`.

## 7. Store assignment: nearest warehouse by straight-line distance
- **Method:** measure the distance from each city to each of the four warehouses (UTM metres), assign each store to the nearest, and keep the runner-up and the margin.
- **Result:** Quito 25 stores (average 26.9 km), Guayaquil 16 (52.6 km), Cuenca 7 (70.6 km), Santo Domingo 6 (48.8 km). The longest distance is 164.6 km.
- **Close calls (margin under 15 km):** Riobamba 7.1 km, Guaranda 8.4, Machala 9.6, Ambato 11.7; 6 stores in all.
- **Rejected for now:** road or drive-time distance (needs a routing service; a stretch goal that would settle the close calls) and weighting stores by sales (comes with the demand forecast).
- **Limits:** straight lines cross the Andes, so a few cities could belong to another warehouse by road.
- **Evidence:** `notebooks/02_gis_foundation.ipynb` Step 6; `data/reference/store_warehouse.csv`.
