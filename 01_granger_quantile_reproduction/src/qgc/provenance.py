"""Where every modelling choice came from.

Four categories, kept strictly distinct so a reader can always tell what the paper
determined from what we decided:

PAPER_SPECIFIED     stated in the target paper (or recoverable from it, e.g. the c
                    grid read off the figure axes)
EXTERNALLY_RESOLVED not in the target paper; resolved from an identified external
                    source, normally the author's own later work
OUR_ASSUMPTION      not determined by any source; our choice, and the result may
                    depend on it
DEVIATION_FROM_PAPER something we knowingly do differently from the paper, e.g. a
                    substituted data source
"""

from __future__ import annotations

from dataclasses import dataclass

PAPER_SPECIFIED = "PAPER_SPECIFIED"
EXTERNALLY_RESOLVED = "EXTERNALLY_RESOLVED"
OUR_ASSUMPTION = "OUR_ASSUMPTION"
DEVIATION_FROM_PAPER = "DEVIATION_FROM_PAPER"


@dataclass(frozen=True)
class Item:
    name: str
    value: str
    classification: str
    source: str


ITEMS: tuple[Item, ...] = (
    Item("Test statistic S_T", "CvM norm of the quantile-marked process, eq. (11)",
         PAPER_SPECIFIED, "Sec. 2.1, eqs. (9)-(11)"),
    Item("Weighting measure F_omega", "d-variate standard normal, giving the closed-form kernel",
         PAPER_SPECIFIED, "Sec. 2.1"),
    Item("Subsample size", "b = [k T^(2/5)], floor", PAPER_SPECIFIED,
         "Sec. 2.2; all nine printed b values reproduce exactly"),
    Item("Subsample count", "B = T - b + 1 overlapping contiguous blocks",
         PAPER_SPECIFIED, "Sec. 2.2 step 1"),
    Item("p-value rule", "p = B^-1 sum 1(S_b,i > S_T), non-recentered",
         PAPER_SPECIFIED, "Sec. 2.2 step 2 (resolution D5)"),
    Item("Quantile grid", "20 equally spaced points on [0.10, 0.90]",
         PAPER_SPECIFIED, "Sec. 4"),
    Item("Monte Carlo replications", "1,000", PAPER_SPECIFIED, "Sec. 4"),
    Item("Sample sizes T", "100, 250, 500", PAPER_SPECIFIED, "Sec. 4"),
    Item("Subsample constants k", "3, 4, 5", PAPER_SPECIFIED, "Sec. 4"),
    Item("DGPs 1-4", "eqs. (13)-(16)", PAPER_SPECIFIED, "Sec. 4"),
    Item("Causality grid c", "0.00, 0.01, 0.03, 0.06, 0.12, 0.24, 0.50",
         PAPER_SPECIFIED, "x-axis tick labels of Figs. 1-4, recovered by rasterising the PDF"),
    Item("Empirical sample", "3 July 2000 to 6 September 2013, T = 3,440",
         PAPER_SPECIFIED, "Sec. 5 and Table 1 note"),
    Item("Empirical transform", "log-differences", PAPER_SPECIFIED, "Sec. 5"),

    Item("sigma specification", "constant sigma, not time-varying",
         EXTERNALLY_RESOLVED, "Troster, Shahbaz & Uddin (2018), MPRA 84194, eq. (15) - resolution D2"),
    Item("Error quantile function", "standard normal inverse CDF; location-shift family",
         EXTERNALLY_RESOLVED, "MPRA 84194, below eq. (15) - resolution D3"),
    Item("QAR(3) specification", "AR(3) + sigma Phi^-1(tau)",
         EXTERNALLY_RESOLVED, "MPRA 84194, eq. (15) - resolution D4"),

    Item("Lags q of Z in I_t", "q = s", OUR_ASSUMPTION,
         "Tables 3-4 label only the lags of I^Y_t (decision C)"),
    Item("k for the empirical tables", "all of 3, 4, 5 reported",
         OUR_ASSUMPTION, "never stated by the paper (decision B)"),
    Item("Standardisation of I_t before the kernel", "standardised",
         OUR_ASSUMPTION,
         "not stated; unstandardised daily log-returns make the kernel ~0.9998 "
         "everywhere, i.e. numerically a matrix of ones - resolution D7"),
    Item("Random seed", "20160604", OUR_ASSUMPTION, "no seed is given anywhere in the paper"),
    Item("Monte Carlo burn-in", "100 observations, series started at zero",
         OUR_ASSUMPTION, "not stated"),
    Item("Mean causality test", "SSR-based F test",
         OUR_ASSUMPTION, "Table 2 does not say which variant was used"),
    Item("ADF / KPSS settings", "AIC lag selection; automatic bandwidth",
         OUR_ASSUMPTION, "not stated; library defaults chosen so nothing is tuned"),
    Item("Sup-Wald critical values", "simulated from sup B(tau)^2/(tau(1-tau))",
         OUR_ASSUMPTION, "the paper does not say which critical values it used"),

    Item("Gold series", "LBMA 15:00 gold fix x 0.583, in place of S&P GSCI Gold Spot",
         DEVIATION_FROM_PAPER,
         "the paper's Datastream series is subscription-only; the proxy matches "
         "Table 1 to <=0.5% and the test is scale-invariant"),
    Item("Oil series", "FRED Europe Brent Spot FOB, in place of Datastream Dated Brent",
         DEVIATION_FROM_PAPER, "closest free equivalent; Table 1 minimum 16.51 vs 17.00 printed"),
    Item("Data alignment", "same-date primary; one-row gold offset also reported",
         DEVIATION_FROM_PAPER,
         "resolution D8 - the paper's Table 2 is only recovered under the offset"),
)


def as_markdown() -> str:
    order = (PAPER_SPECIFIED, EXTERNALLY_RESOLVED, OUR_ASSUMPTION, DEVIATION_FROM_PAPER)
    out = []
    for cls in order:
        items = [i for i in ITEMS if i.classification == cls]
        out.append(f"\n### {cls} ({len(items)})\n")
        out.append("| Item | Value | Source |")
        out.append("|---|---|---|")
        for i in items:
            out.append(f"| {i.name} | {i.value} | {i.source} |")
    return "\n".join(out)
