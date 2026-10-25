# Initial EDA findings

Generated-data inspection: 24 October 2026. Reproduce figures with `python model/scripts/prepare.py` from the project root.

## Dataset and quality

We use UCI Bike Sharing `hour.csv`, not the daily aggregation. The downloaded file contains 17,379 observed hours from 1 January 2011 through 31 December 2012. The hourly date grid contains 17,544 positions: 165 timestamps are absent. There are no missing cells among the observed pre-test rows. Duplicate timestamps are rejected by the loader; target component totals are checked.

The final 90 days start at 2012-10-03 00:00 and end just before 2013-01-01 00:00. Demand plots use only the 15,259 observed pre-test hours. There are 125 absent hours in that earlier period. Missing observations remain NaN: the file does not establish that absent hours mean zero rentals. No held-out target statistics are reported here.

Pre-test hourly demand has median 138, mean 185.39 and maximum 977. This right-skewed distribution motivates examining RMSE alongside MAE: large peak misses can have a substantial operational cost even if average absolute error looks acceptable.

## What the plots show

- Weekday demand has morning and evening peaks; the highest mean working-day hour is 17:00. Non-working days have a broader midday pattern, with highest mean demand at 13:00. Use hour, weekday and working-day context.
- Temperature varies strongly by season and hour. Same-hour temperature has a positive Pearson correlation of about 0.44 with demand; humidity's is about -0.33. These are descriptive associations, confounded by season and calendar patterns.
- Temperature and apparent temperature have correlation about 0.99. They largely overlap in this dataset, but correlation is not a complete feature-selection method.
- Daily mean hourly rentals change across the observation period. Include elapsed time as an initial growth indicator, while recognizing that tree models cannot reliably extrapolate future growth.

Temperature charts use normalized source units. The bundled README says temperature is divided by 41; current UCI web metadata instead describes a min/max conversion. We do not assert a Celsius conversion. Local date/hour labels lack timezone offsets; daylight-saving ambiguity is not resolved by this archive.

## Initial feature decisions

| Feature family | Starting inputs | Reason |
| --- | --- | --- |
| Calendar | Hour, weekday, month, weekend, holiday, working day | Calendar information is known for the target hour |
| Cycles | Sine/cosine of hour, weekday and month | Represent adjacency across midnight and year boundaries |
| Growth | Days since 2011-01-01 | Simple starting indicator for changing demand |
| Recent demand | Lags 1 and 2 hours | Capture current system demand |
| Recurring demand | Lags 24, 48 and 168 hours | Capture daily and weekly repetition |
| Historical summaries | Prior 24/168-hour mean and standard deviation | Describe recent level and variability |

All historical windows are shifted before aggregation. Missing-window statistics are imputed using medians fitted within each training fold. Each model and baseline is scored on the same observed target hours with available lag 1 and lag 168; other missing history can be imputed. Calendar redundancy is deliberate for the first shared feature set and can be assessed with later ablation experiments.

Exclude `casual` and `registered` because their sum is the target. Exclude `instant`, which is a record identifier. Exclude target-hour observed weather because it is unavailable at forecast origin. Past observed weather could be a separate future experiment if its availability is specified. Holiday flags assume a known calendar, not a future observed measurement.

For interviews: **feature usefulness and feature availability are separate questions**. A weather variable may correlate with demand while still being invalid for the chosen prediction contract.
