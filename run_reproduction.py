#!/usr/bin/env python3
"""Single entry point for the Troster (2018) reproduction.

    python run_reproduction.py                 # quick smoke run (default)
    python run_reproduction.py --full          # full reproduction at paper settings
    python run_reproduction.py --profile validation
    python run_reproduction.py --stages mc,supwald --workers 8
    python run_reproduction.py --force mc
    python run_reproduction.py --dry-run --full

This file only ORCHESTRATES. Every piece of science lives in src/qgc/, one
module per responsibility; nothing here computes anything itself.

Stages are cached: a stage is skipped when its manifest hash still matches and
its outputs exist. The profile is part of that hash, so a quick run can never
satisfy a full one.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from config import PROFILE_NAMES, load_profile                      # noqa: E402
from config.base import (                                           # noqa: E402
    DATA_PROCESSED, DATA_RAW, LOGS, MANIFEST_DIR, PAPER_PDF,
    PAPER_TARGETS, RESULTS, RESULTS_FIGURES, RESULTS_TABLES,
)
from qgc.runtime import Manifest, get_logger, stage_key             # noqa: E402

STAGES = ("check", "data", "empirical", "sensitivity", "mc", "supwald",
          "figures", "compare")

#: Rough single-core cost per 1000 replications, measured on an Apple M4.
RUNTIME_HINT = {
    "check": "seconds",
    "data": "seconds (downloads on first run)",
    "empirical": "~30 s",
    "sensitivity": "~5 min (full profile only)",
    "mc": "~8 min single core, ~1 min on 8 workers",
    "supwald": "~155 min single core, ~19 min on 8 workers",
    "figures": "~1 min",
    "compare": "seconds",
}


def build_paths() -> dict[str, Path]:
    return {
        "root": ROOT, "raw": DATA_RAW, "processed": DATA_PROCESSED,
        "results": RESULTS, "tables": RESULTS_TABLES, "figures": RESULTS_FIGURES,
        "paper_targets": PAPER_TARGETS, "paper_pdf": PAPER_PDF, "logs": LOGS,
    }


# --------------------------------------------------------------------- stages
def stage_check(profile, paths, logger) -> list[Path]:
    import numpy as np
    import scipy

    from qgc.runtime.numerics import blas_name

    logger.info("python %s | numpy %s | scipy %s | BLAS %s",
                sys.version.split()[0], np.__version__, scipy.__version__, blas_name())
    if not paths["paper_pdf"].exists():
        logger.warning("paper PDF missing at %s", paths["paper_pdf"])
    for key in ("raw", "processed", "tables", "figures", "logs"):
        paths[key].mkdir(parents=True, exist_ok=True)
    return []


def stage_data(profile, paths, logger) -> list[Path]:
    from qgc.experiments import exp01_summary_stats
    return exp01_summary_stats.run(profile, paths, logger)


def stage_empirical(profile, paths, logger) -> list[Path]:
    from qgc.experiments import exp02_mean_causality, exp03_quantile_causality
    out = exp02_mean_causality.run(profile, paths, logger)
    return out + exp03_quantile_causality.run(profile, paths, logger)


def stage_sensitivity(profile, paths, logger) -> list[Path]:
    from qgc.experiments import exp06_sigma_sensitivity
    return exp06_sigma_sensitivity.run(profile, paths, logger)


def stage_mc(profile, paths, logger) -> list[Path]:
    from qgc.experiments import exp04_monte_carlo
    return exp04_monte_carlo.run(profile, paths, logger)


def stage_supwald(profile, paths, logger) -> list[Path]:
    from qgc.experiments import exp05_supwald_mc
    return exp05_supwald_mc.run(profile, paths, logger)


def stage_figures(profile, paths, logger) -> list[Path]:
    from qgc.reporting import figures
    return figures.run(profile, paths, logger)


def stage_compare(profile, paths, logger) -> list[Path]:
    from qgc.reporting import compare
    return compare.run(profile, paths, logger)


STAGE_FUNCS = {
    "check": stage_check, "data": stage_data, "empirical": stage_empirical,
    "sensitivity": stage_sensitivity,
    "mc": stage_mc, "supwald": stage_supwald, "figures": stage_figures,
    "compare": stage_compare,
}
#: Profile fields each stage actually depends on. Hashing the whole profile would
#: make an unrelated change (say the Monte Carlo c grid) invalidate the data stage.
STAGE_FIELDS = {
    "check": (),
    "data": (),
    "empirical": ("empirical_lags", "k_values", "tau_n", "tau_lo", "tau_hi"),
    "sensitivity": ("run_sigma_sensitivity", "empirical_lags", "tau_n", "tau_lo", "tau_hi"),
    "mc": ("mc_replications", "c_grid", "mc_T", "k_values", "dgps", "qar_orders",
           "tau_n", "tau_lo", "tau_hi", "alpha"),
    "supwald": ("mc_replications", "c_grid", "mc_T", "dgps", "qar_orders",
                "tau_n", "tau_lo", "tau_hi", "alpha"),
    "figures": ("mc_replications", "c_grid", "mc_T", "k_values", "dgps", "qar_orders"),
    "compare": ("mc_replications", "c_grid", "mc_T", "k_values", "dgps",
                "qar_orders", "empirical_lags", "run_sigma_sensitivity"),
}


def stage_profile(profile, stage: str) -> dict:
    """The part of the profile that legitimately affects this stage's output."""
    fields = {f: getattr(profile, f) for f in STAGE_FIELDS[stage]}
    # The profile NAME is always included, so a reduced run can never satisfy a full one.
    fields["profile_name"] = profile.name
    return fields


# A stage's inputs include the upstream stages it depends on.
DEPENDS = {
    "check": (), "data": ("check",), "empirical": ("data",),
    "sensitivity": ("data",),
    "mc": ("check",), "supwald": ("check",),
    "figures": ("mc", "supwald"), "compare": ("empirical", "sensitivity", "figures"),
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", choices=PROFILE_NAMES, default=None)
    ap.add_argument("--quick", action="store_const", const="quick", dest="profile")
    ap.add_argument("--full", action="store_const", const="full", dest="profile")
    ap.add_argument("--stages", default=",".join(STAGES),
                    help=f"comma-separated subset of {','.join(STAGES)}")
    ap.add_argument("--force", default="", help="stage to re-run, or 'all'")
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan and runtime estimates, run nothing")
    args = ap.parse_args(argv)

    profile = load_profile(args.profile or "quick")
    if args.workers:
        object.__setattr__(profile, "workers", args.workers)

    paths = build_paths()
    paths["logs"].mkdir(parents=True, exist_ok=True)
    logger = get_logger("qgc", paths["logs"])
    manifest = Manifest(MANIFEST_DIR, profile.name)

    requested = [s.strip() for s in args.stages.split(",") if s.strip()]
    unknown = set(requested) - set(STAGES)
    if unknown:
        ap.error(f"unknown stage(s): {sorted(unknown)}")

    logger.info("=" * 78)
    logger.info("profile=%s  workers=%d", profile.name, profile.workers)
    logger.info("%s", profile.stamp)
    if not profile.is_paper_reproduction:
        logger.warning("this profile is NOT the paper reproduction; results are "
                       "for pipeline checking only")
    logger.info("=" * 78)

    if args.force == "all":
        manifest.invalidate_all()
        logger.info("invalidated all stage manifests")
    elif args.force:
        for st in args.force.split(","):
            manifest.invalidate(st.strip())
            logger.info("invalidated manifest for stage %r", st.strip())

    if args.dry_run:
        print(f"\nPlan for profile={profile.name}:\n")
        for st in requested:
            key = stage_key(st, stage_profile(profile, st), {"depends": list(DEPENDS[st])})
            state = "CACHED (would skip)" if manifest.is_complete(st, key) else "would RUN"
            print(f"  {st:10s} {state:22s} estimated {RUNTIME_HINT[st]}")
        print("\nNothing executed (--dry-run).\n")
        return 0

    t_start = time.perf_counter()
    for st in requested:
        key = stage_key(st, stage_profile(profile, st), {"depends": list(DEPENDS[st])})
        if manifest.is_complete(st, key):
            logger.info("[%s] cached, skipping (use --force %s to re-run)", st, st)
            continue
        logger.info("[%s] running (estimated %s)", st, RUNTIME_HINT[st])
        t0 = time.perf_counter()
        try:
            outputs = STAGE_FUNCS[st](profile, paths, logger) or []
        except Exception:
            logger.exception("[%s] FAILED", st)
            return 1
        dt = time.perf_counter() - t0
        manifest.mark_complete(st, key, outputs,
                               {"seconds": round(dt, 2), "profile": profile.name})
        logger.info("[%s] done in %.1f s (%d output files)", st, dt, len(outputs))

    logger.info("all requested stages complete in %.1f s", time.perf_counter() - t_start)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
