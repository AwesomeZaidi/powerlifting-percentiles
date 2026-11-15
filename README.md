# Powerlifting percentiles: what 182,030 raw lifters actually total

Squat, bench press, deadlift and total percentiles for every raw full-power (SBD) lifter who competed in 2023–2025, from the [OpenPowerlifting](https://www.openpowerlifting.org) database. The tables are broken down by IPF weight class and by 10 lb bodyweight band. There are also milestone shares, an age curve and year-over-year progression.

Interactive charts and the full write-up: **[splyt.fit/data/what-lifters-total](https://splyt.fit/data/what-lifters-total)**

## Headline numbers

| | Men | Women |
|---|---|---|
| Lifters (each counted once) | 123,060 | 58,970 |
| Median squat | 195 kg (430 lb) | 115 kg (254 lb) |
| Median bench | 125 kg (276 lb) | 61.2 kg (135 lb) |
| Median deadlift | 225 kg (496 lb) | 136.5 kg (301 lb) |
| Median total | 542.5 kg | 312.5 kg |

- 27.4% of male competitors bench 315 lb (three plates), 4.4% bench 405 and 0.4% bench 495.
- 69.1% of men squat 2× bodyweight; 18.8% deadlift 3× bodyweight.
- Among lifters who keep competing, the median man's total is up 7.1% after one year and 15.7% after three. For women it's 8.9% and 20.0%.
- Drug-tested and untested raw lifters total within about 3% of each other at the median.

## Files

| File | What it holds |
|---|---|
| `data/ipf_class_percentiles_kg.csv` | 25th/50th/75th/90th/99th percentile squat, bench, deadlift and total by sex and IPF class |
| `data/bodyweight_band_percentiles_kg.csv` | The same by 10 lb bodyweight band (bands with fewer than 200 lifters dropped) |
| `data/milestones_pct.csv` | Share of lifters hitting plate and bodyweight-multiple milestones |
| `data/age_curve.csv` | Median DOTS and total by 5-year age group |
| `data/progression.csv` | Total gain 1, 2 and 3 years later, for lifters who competed again |
| `data/summary.json` | Everything above in one file, plus tested/untested and single-ply comparisons |
| `scripts/analyze.py` | The script that produced it from the OpenPowerlifting bulk CSV |

## Method

- **Population:** full-power meets (event SBD), raw (sleeves) equipment, a valid three-lift total, recorded bodyweight, meets dated 2023-01-01 to 2025-12-31.
- **One row per lifter:** each lifter counts once, at their best total in the window.
- **Weight classes:** assigned from recorded bodyweight using IPF limits.
- **Progression:** only includes people who competed again, so it is biased toward lifters who stuck with the sport.

To rebuild from the latest data:

```
curl -sSLO https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip && unzip -q openpowerlifting-latest.zip
python3 scripts/analyze.py openpowerlifting-*/openpowerlifting-*.csv data/summary.json
```

## Credit and license

- **Source data:** the [OpenPowerlifting project](https://www.openpowerlifting.org), which places its competition data in the public domain. Thank you to its volunteers.
- **Our aggregates:** released under CC0, so use them however you like. A link back to [splyt.fit/data/what-lifters-total](https://splyt.fit/data/what-lifters-total) is appreciated but not required.
- **Code:** MIT.

Made by [Splyt](https://splyt.fit), a workout tracker for iPhone and Apple Watch. For individual strength tables by bodyweight, see [Splyt's strength standards](https://splyt.fit/strength-standards).
