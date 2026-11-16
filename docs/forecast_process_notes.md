# Forecast process notes (notebook 04, Steps 4 to 6)

This file records how we got from the BREAD/BAKERY table to a forecast: what was done in each step, every option tried, why one was chosen, the numbers, and the limits. The code and results are in `notebooks/04_forecast_bread.ipynb`; the choices are summarised in `docs/decision_log.md` (entry 10). Step 7 of the notebook compares the two forecasts and is written up there.

Derived files used below (`bread_daily.csv`, `results_b.csv`, `results_c.csv`) live in `data/processed/` and are not committed; run the notebook to rebuild them.

---

# Step 4: the BREAD/BAKERY table, the split and the checks

## What I did, in order
1. Staged four files read-only from the PC (perishable_daily_open.csv, perishable_daily_by_warehouse.csv, store_warehouse.csv, holidays_events.csv). I did not touch test.csv or sample_submission.csv. Both processed files were present, so nothing had to be rebuilt.
2. 4a: took BREAD/BAKERY from the "open" file, dates from 2015-01-01, then merged on_promotion (items on promotion that day, summed over the warehouse's stores) from the other file. Checked the merge was one-to-one and lost no rows. Asserted no row is flagged "unusual" (it passed).
3. Computed units_per_open_store = sales / open_stores.
4. 4b: cut the table in time order into train / validation / test and asserted no overlap.
5. 4c: plotly line chart, one line per warehouse, the three periods as pale background bands.
6. 4d (extra cell): gap, holiday and open-store checks.
All cells were run in order from notebooks/ with warnings turned into errors: no warnings, no failures.

## Numbers
- Rows saved: 3,815 (data/processed/bread_daily.csv, 7 columns incl. split). Range 2015-01-01 to 2017-08-15.
- Days per warehouse: Cuenca 953, Quito 953, Santo Domingo 953, Guayaquil 956.
- Dropped warehouse-days with no open store: 9, all Jan 1 (2015, 2016, 2017) for Cuenca, Quito and Santo Domingo. Guayaquil had open stores on Jan 1 each year, so it keeps those rows.
- Dec 25 (2015, 2016) has no rows for any warehouse in the source data at all, so it was never there to drop. (Kaggle's file has no Dec 25.) It is not counted in the 9.

| set | first | last | days | warehouse-days |
|---|---|---|---|---|
| train | 2015-01-01 | 2017-04-25 | 844 | 3,367 |
| validation | 2017-04-26 | 2017-06-20 | 56 | 224 |
| test | 2017-06-21 | 2017-08-15 | 56 | 224 |

Mean units per open store per day: train 481, validation 499, test 490. Warehouse averages: Quito 664, Cuenca 500, Guayaquil 455, Santo Domingo 313 (so warehouses differ a lot in level; a model should know the warehouse).

## Checks
- Gaps: no unexpected missing days in any set. Only the expected absences above (Jan 1 closures in train, Dec 25 missing everywhere). Validation and test are complete: 56 days x 4 warehouses = 224 rows each.
- Test window holidays: no Jan 1. One national day off: 2017-08-11 (the moved celebration of the "Primer Grito de Independencia"; the original date 2017-08-10 is marked transferred=True, so it was NOT a day off). Local holidays also fall in the window (e.g. Santo Domingo on 2017-07-03, Guayaquil 2017-07-24 and 07-25, Riobamba 08-15). Those apply to cities, not whole warehouses, so the modelling step must decide how to use them. I only report them.
- Open stores during validation and test: constant in every warehouse (Quito 25, Guayaquil 16, Cuenca 7, Santo Domingo 6). No new stores, so per-store and total forecasts are equivalent there.

## Options considered and why I chose
- Warehouse-days with no open store: (a) keep as 0 sales, (b) fill with an estimate, (c) drop. A zero would teach a model "demand vanishes on Jan 1" when really nothing was open, and an estimate invents data. I dropped them and listed them. The model is simply not asked to forecast those days.
- Target per open store vs total sales: totals jump when stores open or close, which is not a change in customer demand. Per-open-store units removes that. Total = per-store x open stores, which is known for a future day only if the store plan is known; here it is constant in the final 16 weeks.
- 56-day windows: 56 = 8 whole weeks, so every weekday appears 8 times in each window (bread has a strong weekly pattern; an uneven cut would favour some weekdays). 8 weeks is long enough to smooth out one odd week but short enough to keep most data for training. A random split was rejected: it lets the model see days after the ones it is tested on, which flatters the score. Test is kept last and untouched until the end; validation is for choosing between models.
- Start at 2015-01-01: the Jul-Sep 2014 level rise is unexplained and would mix two different regimes.
- Chart colours: four muted line colours plus grey / blue / orange-tinted bands, kept pale so lines stay readable.

## Limits
- Only 2.6 years of train data; only one winter-holiday season (Dec 2016) per year is seen, so Christmas effects are learned from two examples. The test window is mid-year, so it does not test holiday behaviour at year end.
- on_promotion is a count across all stores in a warehouse; it grows with store count, so Quito's is not comparable to Santo Domingo's. Whether promo for a future day is known in advance is an assumption for the modelling step.
- 8-week test window gives a score that can shift a few percent with a different cut.
- bread_daily.csv must not be committed to GitHub (add to .gitignore if not already covered).

## Findings from reading the saved results together (2026-11-15)
- **Table (4a):** 3,815 rows; 9 January-1 warehouse-days dropped (Cuenca, Quito, Santo Domingo; Guayaquil was open); Dec 25 is absent from the source for all warehouses.
- **Split (4b):** train 844 days, validation 56, test 56, no overlap; 3,367 + 224 + 224 = 3,815.
- **Chart (4c, read from the screenshot):** Quito highest, Santo Domingo lowest, Guayaquil and Cuenca in between; a weekly zigzag in every line; no strong trend from 2015 to mid-2017. Validation and test look like train. The "validation" and "test" band labels overlap at the right edge (cosmetic).
- **Checks (4d):** 0 unexpected gaps; one national day off in the test window (2017-08-11); no Jan 1, Mother's Day or May 1 in the test window; open stores constant in validation and test.
- **Conclusion for Step 4:** the data are complete and the split is fair, but the test window is a mid-year window, so its score will not speak for December or other holiday peaks.
- **Run state:** cells 6a to 6e ran without errors after scikit-learn was installed; 6f, 6g and 7a to 7c had not been run when Step 4 was read.

---

# Step 5: baseline forecasts

## What we are doing and why
Every day a warehouse decides how much bread to stock for TOMORROW. So each forecast is "one day ahead": the forecast for day d may use actual data up to and including day d-1, plus things known in advance (weekday, number of open stores). It never sees day d.
We forecast units per open store, then multiply by the open stores that day to get TOTAL units. All scores are on total units per warehouse-day (224 warehouse-days in validation, 224 in test).
A baseline is a deliberately simple forecast. Its job is to set the bar: the machine-learning model only earns its place if it beats the best baseline by a clear margin.

## Steps (cells 5a to 5f in the notebook)
1. 5a: load bread_daily.csv, put each warehouse on a full calendar so "yesterday" and "same day last week" are simple row shifts.
2. 5b: one `score(df)` function (MAE, WAPE, bias; overall and by warehouse), checked against a hand example.
3. 5c: build eight candidate baselines, run a leakage check, score all on VALIDATION only.
4. 5d: choose the best on validation WAPE (overall).
5. 5e: score ONLY the chosen one plus the plain seasonal naive on TEST, once, and save results_b.csv.
6. 5f: chart of actual vs chosen baseline on test, one panel per warehouse.
Run from notebooks/ with warnings turned into errors: no warnings, no failures.

## Rule for a missing day d-1
Rule chosen: a day with no value takes the value from the same weekday one week earlier (itself filled the same way if needed). Why: bread sales have a strong weekly pattern, so last week's same weekday is a closer stand-in than "the day before" (a missing Sunday filled with Saturday would be wrong). It only looks backwards, so it never uses the future.
Alternatives considered: use the last available day (ignores the weekday pattern); leave it empty and skip the forecast (would drop forecasts for the days after the gap). Rejected for those reasons.
In practice it matters little: 14 gaps got filled (Jan 1 closures in 2016 and 2017 and Dec 25 2015 and 2016 for all warehouses; Jan 1 2015 falls in the first week with no history). Validation and test have no gaps, so no scored day is itself a filled day. The rule only touches the look-back values of a few days in early 2016 and 2017, all in the training period.

## Candidates tried (all one-day-ahead)
| name | forecast for day d (per open store) |
|---|---|
| naive | yesterday's value (d-1) |
| seasonal_naive | same weekday last week (d-7) |
| mean4 / mean8 | average of the last 4 / 8 same weekdays (d-7, d-14, ...) |
| median4 / median8 | ADDED: the median instead of the mean of those same weekdays |
| mean4_level / mean8_level | mean4 / mean8 times (sum of last 7 days / sum of the 7 days before them) |

Why one added candidate (the median): the mean can be pulled by one odd day (a holiday or a promotion spike) in the look-back; the median ignores it. It is the same idea with one change, so it is easy to explain. I added only this one (limit was two). N was chosen on validation among the two values asked for (4 and 8); I did not search other values of N, to avoid fitting the baseline too closely to one 8-week window.
The level adjustment was tried "only if it helps on validation". It did not (below), so it is not used.

Leakage check (in 5c): put a huge number on one day and rebuild all forecasts. The forecast FOR that day does not change for any baseline, so none of them peeks at the day it forecasts.

## Validation results (2017-04-26 to 2017-06-20), sorted by WAPE
| model | MAE (units) | WAPE | bias |
|---|---|---|---|
| median8 | 647.3 | 8.49% | -2.12% |
| mean8 | 648.0 | 8.50% | -1.13% |
| median4 | 649.6 | 8.52% | -2.63% |
| mean4 | 683.7 | 8.96% | -1.52% |
| mean4_level | 764.6 | 10.02% | -0.78% |
| mean8_level | 795.7 | 10.43% | -0.34% |
| seasonal_naive | 920.5 | 12.07% | -0.36% |
| naive | 1405.8 | 18.43% | -0.18% |

WAPE % by warehouse (validation):
| model | Cuenca | Guayaquil | Quito | Santo Domingo |
|---|---|---|---|---|
| naive | 15.90 | 18.67 | 18.43 | 21.92 |
| seasonal_naive | 10.87 | 12.82 | 12.02 | 11.68 |
| mean4 | 7.74 | 9.99 | 8.76 | 8.97 |
| mean8 | 7.29 | 9.53 | 8.25 | 8.75 |
| median4 | 7.54 | 9.98 | 8.02 | 8.98 |
| median8 | 7.02 | 10.15 | 7.93 | 9.47 |
| mean4_level | 9.48 | 10.12 | 10.18 | 9.18 |
| mean8_level | 9.54 | 10.37 | 10.70 | 9.84 |

Bias % by warehouse (validation; positive = over-forecast):
| model | Cuenca | Guayaquil | Quito | Santo Domingo |
|---|---|---|---|---|
| naive | -0.10 | -0.06 | -0.25 | -0.18 |
| seasonal_naive | -0.72 | -0.38 | -0.22 | -0.92 |
| mean4 | -1.82 | -2.86 | -0.67 | -3.40 |
| mean8 | -1.54 | -5.10 | 1.09 | -4.62 |
| median4 | -2.52 | -4.13 | -1.76 | -4.77 |
| median8 | -3.14 | -6.01 | 0.29 | -6.54 |
| mean4_level | -0.80 | -1.71 | -0.25 | -1.80 |
| mean8_level | -0.45 | -3.90 | 1.55 | -2.97 |

## Why median8 was chosen
Rule fixed beforehand: lowest overall validation WAPE. median8 has it (8.49%), 29.7% lower than seasonal naive. But be honest about how close it is: median8 (8.49%), mean8 (8.50%) and median4 (8.52%) are effectively a tie. The difference between them is far smaller than what a different 8-week window would change. The real finding is "average several past same weekdays", not "median beats mean". I followed the rule rather than choosing after the fact. median8 also has the largest negative bias of the top group (-2.12%), mostly in Guayaquil (-6.0%) and Santo Domingo (-6.5%): it under-forecasts there, which means stockout risk. Sales were rising through the validation period, and an 8-week look-back lags behind a rising level.

## Final test results (2017-06-21 to 2017-08-15), scored once
| model | MAE (units) | WAPE | bias |
|---|---|---|---|
| median8 (chosen) | 510.8 | 6.92% | +1.77% |
| seasonal_naive (reference) | 575.3 | 7.80% | +0.91% |

By warehouse:
| warehouse | median8 MAE | median8 WAPE | median8 bias | seasonal naive WAPE | seasonal naive bias |
|---|---|---|---|---|---|
| Cuenca | 224.1 | 6.72% | +2.35% | 7.35% | +1.48% |
| Guayaquil | 535.0 | 6.84% | -2.91% | 9.42% | -1.00% |
| Quito | 1161.1 | 7.12% | +4.47% | 7.16% | +1.85% |
| Santo Domingo | 123.0 | 5.96% | -2.81% | 7.36% | -0.18% |

Test was scored exactly once, only for these two models, after the choice was made on validation. Nothing was changed afterwards.

## What WAPE and bias mean (with an example)
Say one warehouse sells 100 loaves on Monday and 200 on Tuesday (300 in total), and we forecast 120 for Monday and 180 for Tuesday.
- Errors: Monday +20 (we forecast too many), Tuesday -20 (too few).
- WAPE = (|+20| + |-20|) / 300 = 40 / 300 = 13.3%. "On average, the forecast misses by about 13 loaves for every 100 sold." It treats over and under the same, and it is weighted by volume, so big warehouses count more than small ones. Lower is better.
- Bias = (+20 - 20) / 300 = 0%. The misses cancelled out. Bias asks "do we lean one way?". If instead we had forecast 120 and 220, errors +20 and +20, bias = +40/300 = +13.3%: we over-forecast, so bread is left on the shelf (waste). If bias is negative we under-forecast and run out (stockout).
- Why show both: this example has 0% bias yet 13.3% WAPE. A forecast can be right on average and still wrong every single day, and bias alone would hide that.
- MAE (mean absolute error) is the same miss in plain units per warehouse-day (here 20 loaves). It is easy to picture but cannot be compared between a big and a small warehouse, which is why WAPE is the headline.

## How to read the results
- Naive (yesterday) is worst: 18.4%. Bread sells very differently on different weekdays, so yesterday is a poor guide to today.
- Averaging several past same weekdays beats copying one: a single last week carries its own random ups and downs, an average of 4 to 8 weeks smooths them out.
- The level adjustment made things worse, so recent-week momentum is mostly noise at this size.

## Surprises
- The level adjustment hurt on every warehouse (WAPE up 1 to 2 points) because the ratio of two single weeks is itself noisy, and multiplying by it passes that noise into the forecast.
- Test WAPE (6.92%) is lower than validation (8.49%). The test window is simply an easier, steadier stretch; it does not mean the model improved. So compare models within one split, never across splits.
- Naive has the smallest bias but the worst WAPE: another reason to look at both numbers.
- Quito has the largest absolute errors (MAE 1161 units) simply because it is the biggest warehouse; its WAPE is average.

## Limits
- One validation window of 8 weeks: differences of about 0.1 point (median8, mean8, median4) are not meaningful.
- Test contains the 11 Aug national day off and several local holidays; the baselines know nothing about holidays, promotions or open-store changes. A model that does could beat them there.
- The test window is mid-year, so it says nothing about December behaviour.
- Open stores are constant in validation and test, so converting per-store to total adds no error. If stores opened or closed, "known in advance" would be an assumption.
- Forecasts use actual data up to d-1, as in real use. If the data arrives late in practice, a 7-day-lag baseline (seasonal naive) is the safer option.

## What's next and why
The machine-learning model in Step 6 is scored against these numbers: the bar is WAPE 8.49% on validation (median8) and 6.92% on test. Later steps can use the bias numbers to choose stocking levels, since waste and stockout costs are not equal and a deliberate lean is usually wanted.

---

# Step 6: a better model (ridge, gradient boosting, scale-free gradient boosting)

## What we are doing and why
Every day a warehouse decides how much bread to stock for TOMORROW. So every forecast here is "one day ahead": the forecast for day d may use actual data up to and including day d-1, plus things known in advance for day d (weekday, month, day of month, holidays, open stores). We forecast units per open store and multiply by that day's open stores to get TOTAL units; all scores are on total units per warehouse-day.

Three scores, all reusable through one function `score(df)`:
- MAE: average miss in units.
- WAPE (the headline): total absolute miss divided by total actual sales. 5% means the forecasts are off by 5% of sales, in either direction.
- Bias: total (forecast - actual) divided by total actual. Positive = we over-forecast on net (waste risk). Negative = under-forecast (stockout risk). Bias near 0 can hide big errors that cancel out, so read it with WAPE.

## Steps, in order
1. Loaded bread_daily.csv (3,815 rows) and the national holidays file. I never touched the Kaggle contest test.csv or sample_submission.csv.
2. Built features that use only the past (below). 112 rows (the first 28 days of each warehouse) lack a full history and were dropped; 3,703 rows remain.
3. Trained three candidates on `train` only, tried 36 settings in total, scored each on `validation` only.
4. Picked the winner by validation WAPE.
5. Refit the winner on train + validation with its chosen settings and scored `test` ONCE.
6. Permutation importance on validation, and a chart of the test period.

## The features, in plain language
For a day d (all "past" numbers stop at d-1):
- lag1, lag7, lag14, lag21, lag28: units per open store 1, 7, 14, 21, 28 days earlier. lag7 is "same weekday last week".
- mean7, mean28: average of the last 7 and last 28 days. They tell the model the current level of a warehouse.
- same_wd4: average of the last 4 same weekdays (the average of lag7, 14, 21, 28). It is the "typical Sunday" for a Sunday forecast.
- weekday, month, day_of_month: bread has a strong weekly rhythm (Sunday high, Thursday low); day of month is there because paydays (mid-month, month end) may lift buying.
- is_holiday, holiday_tomorrow: national day off today / tomorrow. Only national holidays that were really observed (a holiday "transferred" to another date is counted on the new date, not the old one). Holiday dates are published long in advance, so they are known the day before.
- extra_day: the extra shopping days around Christmas and New Year in the holidays file (they are not days off, so they get their own flag).
- warehouse: because the warehouses differ a lot in size.

Not used on purpose:
- on_promotion. It is the number of items on promotion on day d itself. Nothing shows it is fixed a day ahead, and using it would quietly assume it is. It stays out until we confirm it is known in advance.
- Local and regional holidays. They apply to cities, not whole warehouses, and our warehouses are assumed groupings of stores. A possible later step.
- "Event" days such as Mother's Day (see "What surprised me").

### Rule for missing days
Every warehouse is placed on a complete daily calendar. A missing day (Jan 1 closures, Dec 25, which is absent in the source) is filled with the value from 7 days earlier (same weekday), and if that day is also missing, from 7 days before that. This always uses past data only, keeps the weekly rhythm, and never invents a level. 14 days were filled. Filled days are used only as history for later days; they are never scored (those days are not in the table). Options rejected: leaving a hole (ridge cannot handle it), filling with 0 (teaches that demand vanishes), filling with the previous day (breaks the weekly pattern).

## Candidates and why
(a) Ridge regression: a straight-line model. Each feature adds or subtracts a fixed amount. "Ridge" just means a penalty that keeps the numbers from getting extreme when features overlap (lags are very similar to each other). Uses weekday and warehouse dummies (a yes/no column per weekday and warehouse) plus lags, means, day of month, holiday flags. It is the simple, readable reference.
(b) HistGradientBoostingRegressor on units per open store, with weekday, month and warehouse treated as categories.
(c) Same model, but "scale-free". Why I added it: a tree model can only predict numbers it has seen, and each warehouse has a different size, so trees must learn the level of every warehouse separately and cannot follow a level that drifts. In (c) every lag and average is divided by mean28, the target is "today relative to the last 28 days" (about 1.34 on a typical Sunday), and the forecast is multiplied back by mean28. So a Quito Sunday and a Santo Domingo Sunday look alike to the model, and the model has 4x as many examples of each pattern. That is the only reason it exists; it is not a different learning method.

### What is gradient boosting?
A decision tree asks a chain of yes/no questions ("is it a Sunday? was last Sunday above 800?") and ends in a number. One small tree is crude. Gradient boosting builds many small trees one after another: the first makes a rough guess, the second is trained only on what the first got wrong, the third on what is still wrong, and so on, adding each as a small correction (the "learning rate" says how big a correction is). After a few hundred small trees the sum is a flexible model that can capture things like "Sundays are high, but less so right after a holiday" without us writing that rule. "Hist" means numbers are first sorted into bins, which makes it fast. Settings tuned: learning_rate, max_leaf_nodes (how big each small tree is), max_iter (how many trees), loss (what error is minimised: squared error, or absolute error which matches WAPE more closely).

## Tuning (validation only)
Ridge: alpha in {0.1, 1, 10, 100}. Both HGBs: learning rate {0.05, 0.1} x leaves {8, 16} x trees {150, 300} x loss {squared, absolute} = 16 each. Total 36 settings. Best of each:

| candidate | best settings | validation WAPE | MAE | bias |
|---|---|---|---|---|
| (c) HGB scale-free | lr 0.1, 16 leaves, 300 trees, squared error | 5.88% | 448 | +0.03% |
| (b) HGB plain | lr 0.1, 16 leaves, 300 trees, absolute error | 6.67% | 509 | -0.32% |
| (a) ridge | alpha 0.1 | 7.99% | 610 | -1.10% |
| reference, same weekday last week (not a candidate) | | 12.07% | | |

How to read it: lower WAPE is better. All three beat "same weekday last week" clearly. Both gradient boosters beat the straight-line model, and the scale-free one wins by about 0.8 points. The best settings sit at the edge of the grid (16 leaves, 300 trees), so a larger grid might gain a little; I stopped because of the "few settings" limit and because the top three settings of (c) differ by only 0.02 points. All ridge alphas give nearly identical scores (7.99-8.00%): the penalty hardly matters here.

Validation WAPE by warehouse (each candidate's best setting):

| | ridge | HGB plain | HGB scale-free |
|---|---|---|---|
| ALL | 7.99% | 6.67% | 5.88% |
| Quito | 7.77% | 5.99% | 5.21% |
| Guayaquil | 8.79% | 7.99% | 7.09% |
| Cuenca | 6.99% | 6.45% | 6.41% |
| Santo Domingo | 8.60% | 7.91% | 6.15% |

The ranking is the same in every warehouse. The scale-free version helps most for the small warehouse (Santo Domingo) and least for Cuenca.

Chosen: (c) scale-free HGB, settings as above.

## Final test result (scored once)
Refit on train + validation (3,367 + 224 rows minus the dropped early rows), same settings, forecast each test day from the real values of the days before it.

| | WAPE | MAE (units) | bias |
|---|---|---|---|
| ALL | 3.74% | 276 | +0.49% |
| Quito | 3.02% | 493 | +1.02% |
| Guayaquil | 4.16% | 326 | -0.83% |
| Cuenca | 5.02% | 167 | +0.81% |
| Santo Domingo | 5.72% | 118 | +0.78% |

How to read it: in the test window the forecast was off by about 3.7% of sales, in the net slightly over (+0.5%), so no strong lean toward waste or stockouts. Larger warehouses have the lower percentage error because their daily noise averages out across more stores; the unit error is biggest in Quito simply because it sells the most. Worst test days: 2017-08-12 (10.8%, the Saturday right after the August 11 national day off), 08-15 and 07-15. Test WAPE is lower than validation WAPE; see below for why that should not be read as the model improving.

## What the model leaned on (permutation importance, validation)
Method: shuffle one feature, so it carries no information, and see how many percentage points WAPE rises (average of 20 shuffles). A bigger rise means the model relied on it more. Features that are copies of each other (lags and averages) share credit, so each looks smaller than the group really is.

| feature | WAPE increase (points) |
|---|---|
| mean28 | 11.83 |
| weekday | 6.48 |
| lag1 | 3.09 |
| same_wd4 | 2.35 |
| day_of_month | 2.02 |
| warehouse | 0.71 |
| is_holiday | 0.65 |
| mean7 | 0.61 |
| lag14 / month / lag28 / lag7 / lag21 | 0.42-0.58 |
| holiday_tomorrow | 0.27 |
| extra_day | 0.08 |

What the model learned, in words: (1) the 28-day average sets the level (mean28 is both a feature and the scale used to convert the answer back to units, so shuffling it hurts a lot; do not read 11.8 as pure "information"); (2) the weekday adds the weekly rhythm on top; (3) yesterday and the typical same weekday refine it; (4) day of month matters more than I expected, which is consistent with a payday effect, though it could also be standing in for other monthly patterns; (5) holidays matter a little, and the model has seen few of them, so it cannot learn much more.

## What surprised me
- Day of month mattered more than the holiday flags or last week's value (lag7).
- The two worst validation days were 2017-05-14 (22.6% error) and 2017-05-01 (19.6%). May 14 is Mother's Day in Ecuador, which is an "Event" row in the holidays file that I did not use as a feature; May 1 is Labour Day, but it sits in the train period only twice before, so the model has hardly seen it. Without those two days the validation WAPEs are 7.15% (ridge), 5.74% (plain HGB), 5.16% (scale-free HGB): the ranking does not change, but the validation score is clearly inflated by two special days. The test window contains no Mother's Day or May 1, which is the main reason test looks better than validation.
- The scale-free trick gave a bigger gain than the choice of loss function or any other setting I tuned.

## Limits (be honest about these)
- Scored with ACTUAL lags. In real use, if a forecast is needed more than one day ahead, the lags would themselves be forecasts and the error would grow. This is a one-day-ahead score only.
- Only 56 test days (8 weeks, 224 warehouse-days), one mid-year season, and no Christmas or Mother's Day inside. The score is not a promise for year-end.
- Holiday effects are learned from very few examples (two or three of each holiday in train).
- Only 36 settings were tried; best settings sit at the grid edge. A wider search is possible but would need its own care to avoid fitting the validation window.
- No uncertainty ranges yet: the forecast is one number per day. Stocking decisions need a range or a service-level choice (how often we accept running out), and that is a later step.
- Open stores are assumed known for the next day (they are constant in validation and test).
- Local holidays, Event days (Mother's Day), promotions and weather are not used.
- The warehouses are assumed groupings of stores, not real logistics data.

## What next and why
1. Add Event days (Mother's Day, etc.) and, if justified, local holidays: the biggest validation errors were special days.
2. Turn the point forecast into a range (for example from past errors by weekday), because the stocking decision is about the risk of waste versus stockouts, not the average.
3. Check whether on_promotion is known a day ahead; if so, test it as a feature.
4. Compare with the simple baseline forecasts (step 5b) on the same scoring function before presenting the result.
