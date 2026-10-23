# Decision F - constant sigma (D2) vs AR-GARCH(1,1) sigma

> PROFILE=full - full reproduction at the paper's settings
|    | table   | cause   | effect   | tau         |   lags |   k |   paper_p |   p_constant_sigma |   p_garch_sigma |   difference | same_decision_5pct   |
|---:|:--------|:--------|:---------|:------------|-------:|----:|----------:|-------------------:|----------------:|-------------:|:---------------------|
|  0 | table3  | oil     | gold     | [0.10;0.90] |      1 |   5 |     0     |           0        |        0        |     0        | True                 |
|  1 | table3  | oil     | gold     | 0.10        |      1 |   5 |     0     |           0        |        0        |     0        | True                 |
|  2 | table3  | oil     | gold     | 0.50        |      1 |   5 |     0.294 |           0.058291 |        0.039263 |    -0.019027 | False                |
|  3 | table3  | oil     | gold     | 0.90        |      1 |   5 |     0     |           0        |        0.035337 |     0.035337 | True                 |
|  4 | table3  | usdgbp  | gold     | [0.10;0.90] |      1 |   5 |     0     |           0        |        0        |     0        | True                 |
|  5 | table3  | usdgbp  | gold     | 0.10        |      1 |   5 |     0.011 |           0        |        0        |     0        | True                 |
|  6 | table3  | usdgbp  | gold     | 0.50        |      1 |   5 |     0.004 |           0.051948 |        0.025068 |    -0.02688  | False                |
|  7 | table3  | usdgbp  | gold     | 0.90        |      1 |   5 |     0.01  |           0        |        0.035337 |     0.035337 | True                 |
|  8 | table4  | gold    | oil      | [0.10;0.90] |      1 |   5 |     0     |           0        |        0        |     0        | True                 |
|  9 | table4  | gold    | oil      | 0.10        |      1 |   5 |     0     |           0        |        0.035941 |     0.035941 | True                 |
| 10 | table4  | gold    | oil      | 0.50        |      1 |   5 |     0.461 |           0.456358 |        0.403503 |    -0.052854 | True                 |
| 11 | table4  | gold    | oil      | 0.90        |      1 |   5 |     0     |           0        |        0        |     0        | True                 |
| 12 | table4  | usdgbp  | oil      | [0.10;0.90] |      1 |   5 |     0     |           0        |        0        |     0        | True                 |
| 13 | table4  | usdgbp  | oil      | 0.10        |      1 |   5 |     0.011 |           0        |        0.000604 |     0.000604 | True                 |
| 14 | table4  | usdgbp  | oil      | 0.50        |      1 |   5 |     0.005 |           0.356086 |        0.225914 |    -0.130172 | True                 |
| 15 | table4  | usdgbp  | oil      | 0.90        |      1 |   5 |     0.01  |           0        |        0.012987 |     0.012987 | True                 |
