# Raw data

Source: Kaggle competition "Store Sales - Time Series Forecasting"
https://www.kaggle.com/competitions/store-sales-time-series-forecasting

## How to get it

1. Sign in to Kaggle (free account) and join the competition so you accept
   its rules. Check the rules on reusing the data before publishing anything.
2. Download the data from the competition's Data tab, or from a terminal with
   the Kaggle command-line tool set up:

   ```
   kaggle competitions download -c store-sales-time-series-forecasting
   ```

3. Unzip the files into this folder (`data/raw/`).

## Files expected

`train.csv`, `test.csv`, `stores.csv`, `oil.csv`, `transactions.csv`,
`holidays_events.csv`

The audit in `notebooks/01_data_audit.ipynb` reports what is actually there,
so any difference from this list will show up in its first result.

Do not edit these files. Cleaned versions go in `data/processed/`.
