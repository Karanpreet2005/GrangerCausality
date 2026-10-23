# =============================================================================
#  mqqcause: Multivariate Quantile-on-Quantile Granger Causality
#  Implementation based on the package documentation (mqqcause v1.0.0)
#  Author of package: Dr. Merwan Roudane <merwanroudane920@gmail.com>
#  GitHub: https://github.com/merwanroudane/qqcaus
# =============================================================================

# -----------------------------------------------------------------------------
# STEP 1: Install & load the package
# -----------------------------------------------------------------------------
if (!requireNamespace("mqqcause", quietly = TRUE)) {
  install.packages("mqqcause")
}
library(mqqcause)

# =============================================================================
# SECTION A: BIVARIATE QQ Granger Causality  — qq_causality()
# =============================================================================
# Tests whether the tau-quantile of x_{t-1} Granger-causes
# the theta-quantile of y_t.
#
# FUNCTION SIGNATURE:
#   qq_causality(x, y,
#                y_quantiles = seq(0.05, 0.95, by = 0.05),
#                x_quantiles = seq(0.05, 0.95, by = 0.05),
#                bandwidth = 0.05, n_boot = 200,
#                cdf_based_kernel = TRUE,
#                cause_name = "X", effect_name = "Y",
#                verbose = TRUE, seed = 42)
# -----------------------------------------------------------------------------

set.seed(42)
n <- 200

# --- Simulate toy data -------------------------------------------------------
x <- rnorm(n)                                    # cause variable
y <- 0.3 * c(0, x[-n]) + rnorm(n, sd = 0.4)    # effect (lagged x + noise)

# --- Run bivariate QQ causality ----------------------------------------------
fit_bivariate <- qq_causality(
  x             = x,             # REQUIRED: numeric vector — the CAUSE variable
  y             = y,             # REQUIRED: numeric vector — the EFFECT variable

  y_quantiles   = seq(0.1, 0.9, by = 0.1),  # quantiles of y (theta grid)
  x_quantiles   = seq(0.1, 0.9, by = 0.1),  # quantiles of x (tau   grid)

  bandwidth     = 0.05,          # Gaussian kernel bandwidth on the CDF scale
  n_boot        = 200,           # number of paired-bootstrap replicates
  cdf_based_kernel = TRUE,       # TRUE = use empirical-CDF distance kernel
  cause_name    = "Oil_Price",   # label for x (shown in print/plots)
  effect_name   = "Stock_Return",# label for y (shown in print/plots)
  verbose       = TRUE,          # print progress messages?
  seed          = 42             # RNG seed for reproducibility
)

# --- Inspect results ---------------------------------------------------------
print(fit_bivariate)

# Sup-Wald joint significance test across the full (theta, tau) grid
sw_biv <- sup_wald(fit_bivariate, alpha = 0.05)
print(sw_biv)

# Convert results to a plain numeric matrix (e.g. for export)
t_matrix <- qq_causality_to_matrix(fit_bivariate, value = "t_value")
b_matrix <- qq_causality_to_matrix(fit_bivariate, value = "slope")

# =============================================================================
# SECTION B: MULTIVARIATE (Conditional) QQ Granger Causality — mqq_causality()
# =============================================================================
# Same as Section A but additionally conditions on a vector of moderators Z.
# Optional x*Z interaction terms are also included by default.
#
# FUNCTION SIGNATURE:
#   mqq_causality(x, y, moderators = list(),
#                 y_quantiles = seq(0.05, 0.95, by = 0.05),
#                 x_quantiles = seq(0.05, 0.95, by = 0.05),
#                 bandwidth = 0.05, n_boot = 200, interactions = TRUE,
#                 cdf_based_kernel = TRUE,
#                 cause_name = "X", effect_name = "Y",
#                 verbose = TRUE, seed = 42)
# -----------------------------------------------------------------------------

set.seed(42)
n <- 200

z1 <- rnorm(n)                                        # moderator 1
z2 <- rnorm(n)                                        # moderator 2
x  <- rnorm(n)
y  <- 0.3 * c(0, x[-n]) +
      0.2 * c(0, z1[-n]) +
      rnorm(n, sd = 0.4)

# --- Run multivariate QQ causality -------------------------------------------
fit_multivariate <- mqq_causality(
  x             = x,             # REQUIRED: numeric vector — the CAUSE variable
  y             = y,             # REQUIRED: numeric vector — the EFFECT variable

  moderators    = list(          # REQUIRED (can be empty list for bivariate):
                    Z1 = z1,     #   named list of numeric conditioning vectors
                    Z2 = z2
                  ),

  y_quantiles   = seq(0.1, 0.9, by = 0.1),
  x_quantiles   = seq(0.1, 0.9, by = 0.1),

  bandwidth     = 0.05,
  n_boot        = 200,
  interactions  = TRUE,          # include x*Z cross-terms in the regression?
  cdf_based_kernel = TRUE,
  cause_name    = "Oil_Price",
  effect_name   = "Stock_Return",
  verbose       = TRUE,
  seed          = 42
)

print(fit_multivariate)
sw_mult <- sup_wald(fit_multivariate, alpha = 0.05)
print(sw_mult)

# =============================================================================
# SECTION C: VISUALISATION
# =============================================================================
# All plot functions return a plotly object — assign to a variable or call
# directly to render in the RStudio Viewer.

# --- Heatmap (with significance stars) ---------------------------------------
p_heat <- plot_qq_causality_heatmap(
  qq_result  = fit_bivariate,
  value      = "t_value",     # column to colour-map: "t_value" or "slope"
  colorscale = "Parula",      # colour palette (see mqqcause_colorscales())
  show_stars = TRUE,          # overlay * / ** / *** significance markers?
  x_label    = "X Quantile (tau)",
  y_label    = "Y Quantile (theta)",
  title      = "QQ Granger Causality: Oil Price to Stock Return"
)
p_heat   # renders in RStudio Viewer

# --- 3D Surface --------------------------------------------------------------
p_3d <- plot_qq_causality_3d(
  qq_result    = fit_bivariate,
  value        = "t_value",
  colorscale   = "Parula",
  show_contour = TRUE,        # draw contour lines on the floor of the 3D plot?
  x_label      = "X Quantile (tau)",
  y_label      = "Y Quantile (theta)",
  title        = NULL         # auto-generated if NULL
)
p_3d

# --- Contour plot ------------------------------------------------------------
p_cont <- plot_qq_causality_contour(
  qq_result  = fit_bivariate,
  value      = "t_value",
  colorscale = "Parula",
  x_label    = "X Quantile (tau)",
  y_label    = "Y Quantile (theta)",
  title      = NULL
)
p_cont

# --- Significance-only heatmap -----------------------------------------------
p_sig <- plot_significance_heatmap(
  qq_result  = fit_bivariate,
  colorscale = "Parula"
)
p_sig

# =============================================================================
# SECTION E: AVAILABLE COLOUR SCALES
# =============================================================================
mqqcause_colorscales(show_preview = TRUE)   # print all available palettes

# Preview a specific palette
parula_colors(8)
matlab_jet_colors(8)
turbo_colors(8)
bluered_colors(8)
sinha_colors(8)

# =============================================================================
# SECTION F: LOW-LEVEL BUILDING BLOCKS  (advanced users)
# =============================================================================
# qq_weights()  — compute Gaussian kernel weights for a given quantile tau
w <- qq_weights(x, tau = 0.5, h = 0.05, cdf_based = TRUE)
cat("Sum of weights:", sum(w), "\n")   # should equal length(x)

# gaussian_kernel()  — raw Gaussian kernel on a u-vector
k <- gaussian_kernel(seq(-3, 3, by = 0.5))

# weighted_qr()  — weighted quantile regression via quantreg::rq.wfit
X_mat <- cbind(1, x)
fit_wqr <- weighted_qr(y, X_mat, tau = 0.5, weights = w)
cat("Intercept & slope:", fit_wqr$coef, "\n")
