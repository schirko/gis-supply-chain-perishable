# Perishable Inventory Optimizer (GIS + Supply Chain)

A learning and portfolio project that recommends how many units of a
perishable product each regional warehouse should stock, balancing the cost
of stockouts against the cost of waste, using real grocery sales data and
real geography.

The living project plan (purpose, method, milestones, progress tracker,
glossary) is kept in the Claude doc "Perishable Inventory Optimizer: Project
Plan":
https://claude.ai/code/artifact/15319a10-a679-4c1f-b9b9-c40583dd09da

## Data sources

| Source | Where it lives | Role |
| --- | --- | --- |
| Kaggle "Store Sales - Time Series Forecasting" (Corporacion Favorita, an Ecuadorian grocery chain) | `data/raw/store-sales-time-series-forecasting/` | The project dataset: daily sales by store and product family, store cities, holidays, oil prices and transactions |
| OpenStreetMap (Nominatim geocoder) | `data/reference/city_coordinates.csv` | City coordinates for the 22 store cities, checked against province boundaries (ODbL licence) |
| Natural Earth Admin 1, States and Provinces, 1:10m v5.1.1 | `data/external/` (not committed) | Ecuador's 24 province boundaries (public domain). See `data/external/README.md` for the download and a known Napo/Tungurahua name swap |
| Assumed warehouse sites and store assignment (our own work) | `data/reference/warehouse_sites.csv`, `data/reference/store_warehouse.csv` | Four assumed sites (Quito, Guayaquil, Cuenca, Santo Domingo) and the warehouse for each of the 54 stores. Not the chain's real warehouses. See `docs/decision_log.md` |
| `perishable food supply chain.xlsx` | `data/raw/` (local only) | Not a dataset. A table of model parameters for a multi-stage supply chain optimization. Its source and the meaning of its symbols are still to be confirmed, and it is not used yet |

Raw files are not committed to the repository. See `data/raw/README.md` for
the Kaggle download steps. The spreadsheet stays local until its source is
confirmed.

## Folder layout

```
notebooks/   one numbered notebook per analysis step (code, result, explanation)
modules/     reusable code that the notebooks and the Streamlit app import
data/raw/    original downloaded files (never edited)
data/reference/  small hand-checked lookup tables (city coordinates)
data/external/  third-party boundary files (not committed)
data/processed/  cleaned and aggregated files produced by the notebooks
docs/        project documentation
```

## Milestones

1. Data audit and dataset decision (complete)
2. GIS foundation: warehouse service areas (complete)
3. Demand aggregation and forecast (in progress)
4. Inventory optimization
5. Streamlit app
6. Deploy and write-up

## Findings so far

- **Data:** 54 stores in 22 cities across Ecuador's provinces. 33 product families, of which nine are treated as perishable. Sales are per family, not per item, and sales are not true demand.
- **Geography:** every city point was checked against province boundaries. Two wrong points were found and fixed (Libertad, Ibarra).
- **Regions:** four assumed warehouses (Quito, Guayaquil, Cuenca, Santo Domingo) serve 25, 16, 7 and 6 stores, with the farthest store 164.6 km away. Four cities (6 stores) are close calls, since straight-line distance crosses the Andes.
- **Demand history:** nine perishable families added up by day and warehouse. Quito carries 64.5% of the units, Guayaquil 20.3%, Cuenca 9.7%, Santo Domingo 5.5%. Closed and not-yet-open store days were identified (8 stores opened late; stores close on New Year's Day). Seven families are clean; PRODUCE is unreliable before 2016 and SEAFOOD is small and noisy. Two likely entry errors were flagged.
- **Next:** choose the single family for the first app, then hold out the last weeks as our own test set and compare a baseline forecast with a better model.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
jupyter notebook
```

Open `notebooks/01_data_audit.ipynb` to begin.
