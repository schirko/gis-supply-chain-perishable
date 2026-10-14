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

## 8. Cleaning the demand history: closed stores, unreliable families, outliers
- **What we needed to decide:** which zero and extreme sales values are real demand and which are not, before choosing a family and forecasting.
- **Method:** a store-day with zero sales in all 33 families is treated as not open (before the store's first sale) or closed (after it). We then compared each family's zero share with and without those days, looked at zeros by year, and flagged warehouse-days whose sales per open store were more than 3 times, or less than a third of, the median of the surrounding 29 days.
- **Result:** 6,729 store-days not yet open (8 stores opened after 2013-01-01) and 601 closed (196 of them on four New Year's Days). Seven families (BREAD/BAKERY, DAIRY, DELI, EGGS, MEATS, POULTRY, PREPARED FOODS) have 0.0% zero days once closed days are removed. SEAFOOD has 12.3% zero days and very low volume (about 2.0 million units). PRODUCE has 63% zeros in 2013, 22% in 2014 and 2015, and 0% in 2016 and 2017. 587 of 60,195 checked warehouse-days (1.0%) are unusual, 548 of them PRODUCE. The two clear outliers are MEATS in Cuenca on 2016-10-07 (90,952 units, about 69 times normal) and POULTRY in Santo Domingo on 2015-10-03 (13,057 units, about 13 times normal).
- **Decisions:** (a) count only open stores when computing sales per store; (b) treat PRODUCE before 2016 as unreliable (its zeros look like a recording change; the cause is not confirmed) and SEAFOOD as too small and noisy for the first app, so the first family comes from the seven clean ones; (c) flag the outliers rather than delete rows. Proposed fix, to confirm in Step 3: replace a flagged value with the typical level.
- **Rejected:** a fixed percentile cut-off for outliers (families and warehouses differ too much in size); dropping all zero rows (would also remove real quiet days for slow sellers).
- **Limits:** a day with zero sales in every family could be missing data, not a closure, and we cannot tell the two apart. The cut-off of 3 is a judgement call. The outliers are probably entry errors but we cannot prove it.
- **Evidence:** `notebooks/03_demand_by_warehouse.ipynb` Steps 1 and 2; `data/processed/perishable_daily_by_warehouse.csv` and `perishable_daily_open.csv` (not committed; rebuilt by running the notebook).
