# age_downtime_regression.R
#
# Healthcare Imaging Equipment Utilization & Downtime Analysis
# Month 3 milestone (Mar 2023): statistical test of whether machine age
# significantly predicts total downtime hours.
#
# Input:  outputs/exports/utilization_downtime_by_machine.csv
#         (produced by notebooks/02_utilization_and_downtime_analysis.ipynb)
# Output: outputs/regression_results.txt
#
# Run with:
#   Rscript notebooks/age_downtime_regression.R

data <- read.csv("outputs/exports/utilization_downtime_by_machine.csv")

cat("Rows loaded:", nrow(data), "\n")
cat("Columns:", paste(names(data), collapse = ", "), "\n\n")

# Pearson correlation between machine age and total downtime hours
cor_test <- cor.test(data$age_years, data$total_downtime_hours, method = "pearson")

# Simple linear regression: total_downtime_hours ~ age_years
model <- lm(total_downtime_hours ~ age_years, data = data)
model_summary <- summary(model)

sink("outputs/regression_results.txt")

cat("Healthcare Imaging Equipment Utilization & Downtime Analysis\n")
cat("Statistical test: does machine age predict total downtime hours?\n")
cat(strrep("=", 70), "\n\n")

cat("Sample size (machines):", nrow(data), "\n\n")

cat("--- Pearson correlation (age_years vs total_downtime_hours) ---\n")
cat(sprintf("r = %.4f\n", cor_test$estimate))
cat(sprintf("p-value = %.4f\n", cor_test$p.value))
cat(sprintf("95%% CI = [%.4f, %.4f]\n\n", cor_test$conf.int[1], cor_test$conf.int[2]))

cat("--- Linear regression: total_downtime_hours ~ age_years ---\n")
print(model_summary)

cat("\n--- Interpretation ---\n")
alpha <- 0.05
r_val <- unname(cor_test$estimate)
p_val <- cor_test$p.value
slope <- unname(coef(model)["age_years"])

if (p_val < alpha) {
  significance_text <- sprintf(
    "Statistically significant at alpha = 0.05 (p = %.4f). Machine age is associated with total downtime hours.",
    p_val
  )
} else {
  significance_text <- sprintf(
    "Not statistically significant at alpha = 0.05 (p = %.4f). We cannot reject the null hypothesis that age has no linear relationship with downtime in this sample.",
    p_val
  )
}
cat(significance_text, "\n")

direction_text <- if (r_val > 0) "positive" else "negative"
cat(sprintf(
  "Correlation direction: %s (r = %.3f). On average, each additional year of age is associated with a change of %.2f downtime hours over the observation window, holding the simple linear model's assumptions.\n",
  direction_text, r_val, slope
))

cat(sprintf(
  "R-squared = %.3f: age alone explains %.1f%% of the variance in total downtime hours across the fleet.\n",
  model_summary$r.squared, model_summary$r.squared * 100
))

sink()

cat("\nWrote outputs/regression_results.txt\n")
