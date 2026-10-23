# Quantile_Economics

Work on Granger causality in quantiles and related quantile-based methods for
economic and financial time series. Each numbered folder is a self-contained
project with its own README, environment and results.

| Folder | What it is |
|---|---|
| [`01_granger_quantile_reproduction/`](01_granger_quantile_reproduction/README.md) | Clean-room Python reproduction of Troster (2018), *Testing for Granger-causality in quantiles*, Econometric Reviews 37(8). Tables 1-4, Monte Carlo Figs. 1-4, comparison report. |
| [`02_mqqcause_analysis/`](02_mqqcause_analysis/) | Exploratory analysis with the `mqqcause` R package (quantile-on-quantile Granger causality): R script, R and Python notebooks, sample data, package manual. |

New work goes in the next numbered folder (`03_...`), with its own README.

## Working on a project

Run commands from inside the project folder; paths there are relative to it.

```bash
cd 01_granger_quantile_reproduction
make setup      # first time only: creates .venv
make test
make quick      # smoke run -> results/quick/
```
