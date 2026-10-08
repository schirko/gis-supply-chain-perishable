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
| `perishable food supply chain.xlsx` | `data/raw/` (local only) | Not a dataset. A table of model parameters for a multi-stage supply chain optimization. Its source and the meaning of its symbols are still to be confirmed, and it is not used yet |

Raw files are not committed to the repository. See `data/raw/README.md` for
the Kaggle download steps. The spreadsheet stays local until its source is
confirmed.

## Folder layout

```
notebooks/   one numbered notebook per analysis step (code, result, explanation)
modules/     reusable code that the notebooks and the Streamlit app import
data/raw/    original downloaded files (never edited)
data/processed/  cleaned and aggregated files produced by the notebooks
docs/        project documentation
```

## Milestones

1. Data audit and dataset decision (in progress: dataset chosen)
2. GIS foundation: warehouse service areas
3. Demand aggregation and forecast
4. Inventory optimization
5. Streamlit app
6. Deploy and write-up

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
jupyter notebook
```

Open `notebooks/01_data_audit.ipynb` to begin.
