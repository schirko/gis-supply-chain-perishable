# Perishable Inventory Optimizer (GIS + Supply Chain)

A learning and portfolio project that recommends how many units of a
perishable product each regional warehouse should stock, balancing the cost
of stockouts against the cost of waste, using real grocery sales data and
real geography.

The living project plan (purpose, method, milestones, progress tracker,
glossary) is kept in the Claude doc "Perishable Inventory Optimizer: Project
Plan":
https://claude.ai/code/artifact/15319a10-a679-4c1f-b9b9-c40583dd09da

## Data

Kaggle "Store Sales - Time Series Forecasting" (Corporacion Favorita, an
Ecuadorian grocery chain). See `data/raw/README.md` for download steps.
Raw data is not committed to the repository.

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
