"""Development / smoke profile. Verifies the pipeline runs; proves nothing."""

from .base import Profile

PROFILE = Profile(
    name="quick",
    mc_replications=25,
    c_grid=(0.0, 0.12),
    mc_T=(100,),
    k_values=(3,),
    dgps=(1,),
    qar_orders=(1,),
    empirical_lags=(1,),
    run_sigma_sensitivity=False,
)
