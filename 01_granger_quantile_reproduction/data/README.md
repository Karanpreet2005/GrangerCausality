# Data provenance

The paper draws all three series from **Datastream**, which is subscription-only.
Every series here is rebuilt from a free public source and validated against the
paper's Table 1 before any analysis runs.

| Series | Source | Status | Notes |
|---|---|---|---|
| `usdgbp` | FRED `DEXUSUK` | **exact** | Matches all seven Table 1 values at the printed 2 dp. |
| `oil` | FRED `DCOILBRENTEU` (Europe Brent Spot FOB) | **near-exact proxy** | Stands in for Datastream's Platts "Crude Oil Dated Brent". Table 1 minimum is 16.51 against 17.00 printed; other moments agree to under 1%. |
| `gold` | LBMA 15:00 gold fix (`prices.lbma.org.uk/json/gold_pm.json`), scaled by 0.583 | **near-exact proxy** | The paper uses the S&P GSCI Gold Spot index, which is not freely available (Yahoo carries no history for `^SPGSGC`; Barchart requires a paid plan). |

## The gold scale factor

The S&P GSCI Gold Spot index is a scalar multiple of the gold spot price over this
window. The ratios implied by Table 1's mean, minimum and maximum are 0.5838,
0.5837 and 0.5813 - agreeing to about 0.4%, which is what identifies the
relationship as a pure change of units.

The factor is a **units conversion, not a fitted parameter**. The test runs on
log-differences and is exactly invariant to any positive scaling, so 0.583 moves
the Table 1 level statistics and nothing else. No p-value anywhere depends on it.

## Calendar

Datastream's daily convention is a five-day week with holidays carried forward.
That is reproduced as a business-day index plus forward fill, which yields exactly
**3,440** rows over 2000-07-03 to 2013-09-06 - the paper's stated sample size.

## Alignment (resolution D8)

The paper's Table 2 does not reproduce when all three series are aligned on the
same trading date, but reproduces completely (12/12 cells) when the gold series is
offset by one trading row. Both alignments are computed and reported. The offset is
**not** adopted silently.

## Licences and reuse

FRED series are US federal government data, free to use. LBMA benchmark prices are
published for public reference; check LBMA's terms before redistributing the raw
file. Neither raw download is committed to git - both are refetched by
`python run_reproduction.py --stages data`.

## Using your own data

Sources are pluggable; see `src/qgc/data/providers/` and `src/qgc/data/datasets.py`.
Swapping in a Datastream export is a one-line change:

```python
DATASETS["troster2018"].series["gold"] = CsvFile("data/raw/my_gsci_gold.csv")
```
