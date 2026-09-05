"""Every choice NOT decided by the target paper, with its source.

The target paper is Troster (2018), Econometric Reviews 37(8), 850-866. Where it
is silent or internally inconsistent, the resolution is recorded here rather than
buried in the implementation, so a reader can always tell paper from judgement.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Resolution:
    tag: str
    issue: str
    resolution: str
    source: str


RESOLUTIONS: tuple[Resolution, ...] = (
    Resolution(
        tag="D1",
        issue=(
            "Sec. 5 text calls the gold series 'S&P gold prices (per ounce)' while the "
            "Table 1 note calls it the 'S&P GSCI Gold Spot price index'. Table 1's "
            "magnitudes (149-1101) match the index, not USD/oz (256-1895)."
        ),
        resolution=(
            "Treat it as the index. Immaterial for the test, which runs on "
            "log-differences and is therefore invariant to the scale factor."
        ),
        source="Target paper, Sec. 5 and Table 1 note (p. 863), read against each other.",
    ),
    Resolution(
        tag="D2",
        issue="Eq. (17) writes a time-varying sigma_t but defines no volatility model.",
        resolution=(
            "Use a constant sigma as the primary specification; the 't' subscript is "
            "treated as a typographical artifact. An AR(p)-GARCH(1,1) variant is run as "
            "a sensitivity on the empirical tables only."
        ),
        source=(
            "Troster, Shahbaz & Uddin (2018), MPRA 84194, eq. (15), which restates the "
            "same models as '... + sigma*Phi^-1(tau)' with theta(tau) = (mu0, mu1, mu2, mu3, sigma)'."
        ),
    ),
    Resolution(
        tag="D3",
        issue="Eq. (17) does not say which error distribution Phi_eps^-1 refers to.",
        resolution=(
            "Standard normal. The model is therefore a location-shift family: the mu "
            "coefficients do not vary with tau, and one Gaussian ML fit serves the whole "
            "tau grid. Conditional quantile = fitted AR mean + sigma_hat * Phi^-1(tau)."
        ),
        source=(
            "Troster, Shahbaz & Uddin (2018), MPRA 84194, below eq. (15): 'Phi^-1(.) is "
            "the inverse of a standard normal distribution function'."
        ),
    ),
    Resolution(
        tag="D4",
        issue="Tables 3-4 use a 3-lag column but eq. (17) defines only QAR(1) and QAR(2).",
        resolution="QAR(3) = AR(3) plus sigma*Phi^-1(tau), by direct extension.",
        source="Troster, Shahbaz & Uddin (2018), MPRA 84194, eq. (15), 'QAR3'.",
    ),
    Resolution(
        tag="D5",
        issue=(
            "The author's later paper describes p-values as 'averaging the subsample test "
            "statistics'; the target paper defines critical values through the subsample "
            "CDF G_hat, i.e. an average of indicators."
        ),
        resolution="Follow the target paper: p = B^-1 * sum_i 1(S_{b,i} > S_T).",
        source="Target paper, Sec. 2.2, step 2.",
    ),
    Resolution(
        tag="D6",
        issue="The absolute value in eq. (11) is redundant.",
        resolution=(
            "Implemented as written. W is a real symmetric positive semi-definite "
            "Gaussian kernel and psi is real, so psi'W psi >= 0 always; a unit test "
            "asserts this."
        ),
        source="Target paper, eq. (11); standard property of the Gaussian kernel.",
    ),
    Resolution(
        tag="D7",
        issue=(
            "The paper does not say whether the conditioning vector I_t is standardised "
            "before entering the kernel W_{t,s} = exp[-0.5 (I_t - I_s)^2]. This matters "
            "enormously for the empirical application: daily log-returns are O(0.01), so "
            "||I_t - I_s||^2 is O(1e-4) and the literal kernel is ~0.9998 everywhere, "
            "leaving W numerically indistinguishable from a matrix of ones. The Monte "
            "Carlo is unaffected because its DGPs already have unit variance."
        ),
        resolution=(
            "Standardise each component of I_t to zero mean and unit variance by default, "
            "which is the usual practice for this family of characteristic-function tests. "
            "The unstandardised kernel is retained behind a flag and BOTH are reported for "
            "the empirical tables, so the choice is visible rather than assumed."
        ),
        source=(
            "Our own numerical analysis of the empirical series (this is NOT resolved by "
            "any Troster paper). Escanciano & Velasco (2006), on whose construction eq. "
            "(11) is based, work with standardised regressors."
        ),
    ),
)


def as_markdown() -> str:
    rows = ["| Tag | Issue | Resolution | Source |", "|---|---|---|---|"]
    for r in RESOLUTIONS:
        clean = lambda s: s.replace("\n", " ").replace("|", "\\|")
        rows.append(f"| {r.tag} | {clean(r.issue)} | {clean(r.resolution)} | {clean(r.source)} |")
    return "\n".join(rows)


if __name__ == "__main__":
    print(as_markdown())
