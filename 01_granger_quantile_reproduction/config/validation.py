"""Intermediate profile. Checks stability before committing to the full run."""

from .base import Profile

PROFILE = Profile(
    name="validation",
    mc_replications=250,
    c_grid=(0.0, 0.03, 0.12, 0.50),
    mc_T=(100, 500),
    k_values=(3, 5),
    dgps=(1, 2, 3),
    qar_orders=(1, 2),
    empirical_lags=(1, 3),
    run_sigma_sensitivity=False,
)
