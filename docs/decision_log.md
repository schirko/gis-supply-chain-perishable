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

## 9. First product family: BREAD/BAKERY, trained on 2015 onward
- **What we needed to decide:** the single perishable family the first app builds its forecast and stocking recommendation around.
- **Method:** started from the seven families with trustworthy zeros (decision 8), replaced the 32 flagged outlier days with the typical level, and compared the families on size, weekly and daily variation, weekday pattern and growth (table), then looked at each family's whole weekly history (charts) and weekday pattern (heatmap). Shelf life is general knowledge, not from the data.
- **Result:** BREAD/BAKERY has the lowest weekly variation (0.066) and daily noise (0.097), no flagged days, and a strong weekly rhythm (Sunday 34% above average, Thursday 20% below). DAIRY and POULTRY both roughly double in the same week in mid-November 2013, which looks like a recording change. DELI and EGGS drift and step; PREPARED FOODS is small and dropped in 2017; MEATS is flat all through and the second steadiest.
- **Chosen:** BREAD/BAKERY, using 2015-01-01 onward (about 953 days per warehouse). MEATS is the runner-up and a candidate for a later app.
- **Rejected:** MEATS (13 flagged days including a large entry error, weaker waste story), DAIRY and POULTRY (2013 level change), DELI and EGGS (unstable), PREPARED FOODS (small, 2017 drop), PRODUCE and SEAFOOD (decision 8). Also rejected: picking from the comparison table alone, since it only covers 2016 onward and missed the level changes the charts showed.
- **Limits:** BREAD/BAKERY rises about 25 to 30% between July and September 2014, in all four warehouses (19% to 27% higher from 2015 on than in early 2014). We cannot say whether it is real growth or a recording change, so we avoid it by starting in 2015, and we cannot rule out another change later. The cause of the DAIRY and POULTRY jump is not confirmed. Santo Domingo is the noisiest warehouse (weekly variation 0.11 against about 0.08).
- **Evidence:** `notebooks/03_demand_by_warehouse.ipynb` Step 3 (cells 3a to 3d and the Step 3 decision).

## 10. How we test and score the BREAD/BAKERY forecast
- **What we needed to decide:** how to build the forecast table, how to split the data, what to score, and what counts as "better".
- **Method:** BREAD/BAKERY from 2015-01-01, one row per warehouse and open day. We predict units per open store and multiply by the open stores for the total. Split by date, in time order: test = the last 56 days (2017-06-21 to 2017-08-15), validation = the 56 days before (2017-04-26 to 2017-06-20), train = everything earlier. Forecasts are one day ahead (day d may use data up to d-1 plus what is known in advance). Scores are on total units per warehouse-day: WAPE (headline), MAE and bias. Choices are made on validation; the test weeks are scored once at the end.
- **Result of the baselines and the model (test weeks, scored once):** seasonal naive (same weekday last week) WAPE 7.80%; best simple baseline, the median of the last 8 same weekdays, 6.92% (bias +1.77%); scale-free gradient boosting 3.74% (bias +0.49%), about 46% less error than the baseline. On validation the three finished at 12.07%, 8.49% and 5.88%. Test numbers are lower than validation because the test window contains neither Mother's Day nor May 1, so numbers are only comparable within one window.
- **Rejected:** a random split (lets a model see days after the ones it is tested on); total units as the target (jumps when stores open or close); keeping or filling the 9 Jan 1 warehouse-days with no open store (zeros teach "demand vanishes", fills invent data); promotions as a feature (not shown to be known a day ahead); local holidays and Event days such as Mother's Day (not used yet); a wider N for the baseline or a wider settings grid for the model (to avoid fitting one 8-week window).
- **Limits:** one-day-ahead scores use actual earlier values; a longer horizon would be worse. Only 56 test days, mid-year, with no year-end. Holiday effects are learned from very few examples. The forecast is one number per day, with no range yet, and stocking decisions need a range. Open stores are assumed known a day ahead.
- **Evidence:** `notebooks/04_forecast_bread.ipynb` Steps 4 to 7; `docs/forecast_process_notes.md`.

## 11. Public project page on the portfolio (schirko.com/scott/gis-supply-chain/perishable/)
- **Chosen:** copy the recipe used by the meat-prices project. `python -m src.build_site` redraws two charts from `data/processed/bread_daily.csv`, fills the headline numbers from `src/site_facts.json` into `src/site_template.html`, exports each notebook that has saved outputs as an HTML page, turns `docs/decision_log.md` and `docs/forecast_process_notes.md` into pages, and adds a back bar and a noindex tag to every page.
- **Where it goes:** `SITE_DIR` in `.env` points at `Schirko\scott\gis-supply-chain\perishable`. The portfolio project serves that folder publicly (noindex) and redeploys on push. With no `SITE_DIR`, the build writes to the git-ignored `site/`.
- **Rejected:** a public GitHub Pages site (the portfolio is the one public home) and screenshots of notebooks (HTML export keeps the real outputs and the plotly maps interactive).
- **Safeguards:** a notebook with an error output or with code cells never run is not published (the build prints a warning). A notebook whose explanation cells still say "Fill in together" is published without those cells, tagged "in progress", with a banner.
- **Limit:** the headline test numbers are typed into `src/site_facts.json` (from entry 10), not recomputed, because the test predictions are produced inside notebook 04. Update that file if the forecast changes.
- **Repo stays public:** the front page and the portfolio card both keep a "View code on GitHub" link.

## 12. This project never writes the portfolio's index.html (standing rule, 2026-11-16)
- **Rule:** this project owns only `scott/gis-supply-chain/perishable/` and its card screenshot in `scott/images/screenshots/`. The portfolio project owns `scott/index.html`, `styles.css` and `backbar.css`. If the portfolio card needs a change, we give the portfolio project the new text and it makes the edit.
- **What the build does:** every file `python -m src.build_site` writes or deletes is inside `SITE_DIR`. It never touches `scott/index.html`, so no build step had to be removed.
- **Safeguard added:** the build refuses to run if `SITE_DIR` looks like the portfolio root (a folder named `scott`, or one that contains `styles.css` or `backbar.css`), so a wrong `.env` cannot overwrite or clean it.
- **History:** before this rule, on 2026-11-15, the card text and a change-log row in the portfolio's development guide were edited from this project. That will not happen again.
