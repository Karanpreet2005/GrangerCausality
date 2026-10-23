#!/usr/bin/env Rscript
# ---------------------------------------------------------------------------
# Independent robustness check using the `mqqcause` package (Roudane, CRAN,
# 2026), which implements Sim & Zhou (2015) quantile-on-quantile regression
# plus a Bonferroni-corrected max-|t| aggregate test.
#
# THIS IS NOT A REIMPLEMENTATION OF TROSTER (2018). It is a different,
# independently-coded method run on the same series, to see whether a
# differently-specified test agrees on the qualitative causal pattern. See
# robustness/README.md for the full comparison and caveats.
# ---------------------------------------------------------------------------

.libPaths(c("robustness/rlib", .libPaths()))
suppressMessages(library(mqqcause))

set.seed(20160604)  # same convention as the Python reproduction

d <- read.csv("data/processed/logdiff.csv")
cat(sprintf("Loaded %d observations (%s to %s)\n", nrow(d), d$date[1], d$date[nrow(d)]))

directions <- list(
  list(cause = "oil",    effect = "gold", x = d$oil,    y = d$gold),
  list(cause = "usdgbp", effect = "gold", x = d$usdgbp, y = d$gold),
  list(cause = "gold",   effect = "oil",  x = d$gold,    y = d$oil),
  list(cause = "usdgbp", effect = "oil",  x = d$usdgbp, y = d$oil)
)

all_results <- list()
sup_wald_summary <- list()

for (dir in directions) {
  tag <- paste0(dir$cause, "_to_", dir$effect)
  cat(sprintf("\n=== %s -> %s ===\n", dir$cause, dir$effect))

  fit <- qq_causality(dir$x, dir$y,
                       y_quantiles = seq(0.05, 0.95, by = 0.05),
                       x_quantiles = seq(0.05, 0.95, by = 0.05),
                       bandwidth = 0.05, n_boot = 200,
                       cause_name = dir$cause, effect_name = dir$effect,
                       verbose = FALSE, seed = 20160604)

  res <- fit$results
  res$direction <- tag
  all_results[[tag]] <- res

  sw <- sup_wald(fit)
  sup_wald_summary[[tag]] <- data.frame(
    direction = tag,
    sup_t = sw$sup_statistic,
    at_y_quantile = sw$argmax_y_quantile,
    at_x_quantile = sw$argmax_x_quantile,
    bonferroni_p = sw$bonferroni_p_value,
    reject_5pct = sw$reject_H0_at_alpha
  )
  cat(sprintf("  Sup-|t| = %.3f at (Y_tau=%.2f, X_theta=%.2f), Bonferroni p = %.4f, reject@5%% = %s\n",
              sw$sup_statistic, sw$argmax_y_quantile, sw$argmax_x_quantile,
              sw$bonferroni_p_value, sw$reject_H0_at_alpha))

  # Row at X's own median (theta = 0.5) is the closest analogue to Troster's
  # univariate framing: how Y's quantile responds to X, evaluated near X's
  # typical (median) value rather than X's own tail.
  at_median_x <- res[abs(res$x_quantile - 0.5) < 1e-6, ]
  for (yq in c(0.10, 0.50, 0.90)) {
    row <- at_median_x[abs(at_median_x$y_quantile - yq) < 1e-6, ]
    if (nrow(row) == 1) {
      cat(sprintf("    Y_tau=%.2f | X at its median: beta1=%.4f t=%.3f p=%.4f\n",
                  yq, row$beta1, row$t_value, row$p_value))
    }
  }
}

full <- do.call(rbind, all_results)
write.csv(full, "robustness/output/qqcause_full_grid.csv", row.names = FALSE)

sw_all <- do.call(rbind, sup_wald_summary)
write.csv(sw_all, "robustness/output/qqcause_sup_wald_summary.csv", row.names = FALSE)

cat("\n=== Sup-Wald summary across all four directions ===\n")
print(sw_all, row.names = FALSE)

cat("\nWrote robustness/output/qqcause_full_grid.csv and qqcause_sup_wald_summary.csv\n")
