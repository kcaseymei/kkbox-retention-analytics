# Churn prediction results (stage E)

Date: 2026-10-12. Reproduce: `python -m src.run_experiments` (about 25 minutes), `python -m src.run_ablation` (about 10 minutes), `python -m src.model_report` (figure); the saved tables are in `reports/model_results/`. Design and leakage controls: [prediction_design.md](../docs/prediction_design.md); model card: [model_card.md](../docs/model_card.md).

**Evidence:** full-data results on every user of each evaluated month (training uses a random sample of 100,000 users per month). Descriptive and predictive associations only, not causal effects. Settings were fixed in advance (no tuning), so the test months were never used to choose anything.

## Protocol

| Role | Months | Labels | Training data |
|---|---|---|---|
| Validation | 2016-07 to 2016-12 (6 months) | rebuilt | all months up to the purge limit (11 to 16 months) |
| Final test | 2017-01, 2017-02 | rebuilt | 17 and 18 months |
| External check | 2017-03 | **official** `train_v2` (different treatment of early renewers) | 18 months, up to 2016-12 |

Training months must have complete labels by the cutoff of the evaluated month (`leakage_checks.check_purge`); for March this excludes January. Capacity K is 5%, 10% and 20% of the month's expiring users. A random list reaches K% of the churners (lift 1).

## Models compared

- **Rule: no auto-renew** — flags users whose last transaction has auto-renew off (the baseline to beat).
- **Rule: few transactions**, **rule: few listening days (30 days)** — one-feature rules.
- **Logistic regression** and **gradient boosting** on 57 features (31 listening, 20 subscription, 6 profile); fixed settings.

## Results at the validation months (mean of 6 months)

| Model | Recall at 5% | at 10% | at 20% | Lift at 5% | Lift at 10% | AUC |
|---|---|---|---|---|---|---|
| Gradient boosting | 50.7% | 71.6% | 84.5% | 10.1 | 7.2 | 0.899 |
| Logistic regression | 50.9% | 70.9% | 83.7% | 10.2 | 7.1 | 0.898 |
| Rule: no auto-renew | 24.5% | 49.2% | 74.4% | 4.9 | 4.9 | 0.809 |
| Rule: few transactions | 28.5% | 46.0% | 60.6% | 5.7 | 4.6 | 0.774 |
| Rule: few listening days | 5.4% | 10.7% | 21.5% | 1.1 | 1.1 | 0.589 |

## Final test (rebuilt labels)

| Month (churn rate) | Model | Recall at 5% | at 10% | at 20% | Lift at 10% | AUC |
|---|---|---|---|---|---|---|
| 2017-01 (4.51%) | Gradient boosting | 49.0% | 71.9% | 82.1% | 7.19 | 0.885 |
| | Logistic regression | 52.6% | 71.1% | 81.0% | 7.11 | 0.882 |
| | Rule: no auto-renew | 26.3% | 52.5% | 72.3% | 5.25 | 0.796 |
| 2017-02 (3.95%) | Gradient boosting | 48.5% | 68.1% | 78.8% | 6.81 | 0.865 |
| | Logistic regression | 48.5% | 67.7% | 77.3% | 6.77 | 0.861 |
| | Rule: no auto-renew | 26.8% | 54.2% | 67.6% | 5.42 | 0.773 |

Contacting 10% of February's expiring users with the gradient boosting list reaches 68.1% of the churners, against 54.2% for the auto-renew rule and 10% for a random list. Lift is highest at the top of the list (9.7 at 5%).

## External check: March 2017 (official labels, churn rate 8.99%)

| Model | Recall at 5% | at 10% | at 20% | Lift at 10% | AUC |
|---|---|---|---|---|---|
| Gradient boosting | 27.9% | 44.9% | 65.6% | 4.49 | 0.810 |
| Logistic regression | 18.7% | 33.9% | 65.7% | 3.39 | 0.773 |
| Rule: no auto-renew | 22.9% | 45.9% | 58.4% | 4.59 | 0.733 |

**On the official March labels the model does not clearly beat the auto-renew rule at 10%** (44.9% against 45.9%); it is better at 5% (27.9% against 22.9%) and 20% (65.6% against 58.4%), and its AUC is higher (0.810 against 0.733). Performance is much lower than on the rebuilt months. Part of the reason is the population: 108,802 of the 970,960 official users have a last expiration outside March (or no history at the cutoff) and fall outside the rebuilt rule; their churn rate is 22.7% and they are not on the 1 to 31 day lead-time scale. The remaining difference is the labeling of early renewers (open question). Calibration is also off in March: in the highest-risk bins the observed churn rate is higher than predicted (for example 18.6% observed against 11.4% predicted in the ninth decile).

## Which features matter (ablation, gradient boosting)

| Features | Recall at 10%, Jan | Feb | Mar | AUC Jan | Feb | Mar |
|---|---|---|---|---|---|---|
| All | 71.9% | 68.1% | 44.9% | 0.885 | 0.865 | 0.810 |
| Subscription + profile (no listening) | 70.8% | 66.9% | 52.0% | 0.881 | 0.857 | 0.815 |
| Subscription only | 70.7% | 66.8% | 52.6% | 0.880 | 0.857 | 0.812 |
| Listening only | 30.0% | 27.6% | 16.4% | 0.665 | 0.632 | 0.540 |

- **Listening behavior carries signal on its own** (3 times the random list at 10% in January and February, AUC 0.63 to 0.66) **but adds little on top of the subscription record**: about 1 point of recall at 10% and less than 0.01 AUC in the rebuilt months, and nothing in March (the model without listening is better there).
- **The profile columns (members snapshot) add no consistent gain**: the mean recall at 10% over the six validation months is 71.6% for gradient boosting with and without them, and the test months differ by 0.3 points or less at 10% in January and February (in March the version without them is 1.7 points better; at 5% in January 3.7 points better). So the model does not rely on the pattern of missing profiles (which could otherwise leak whether a member profile exists).
- Permutation importance (gradient boosting, January 2017): the last payment method code is by far the largest (AUC drop 0.093), then days since the last transaction (0.012), number of transactions (0.007), auto-renew (0.005), and whether the last row is a cancellation (0.005). What the payment method code means is unknown (no meanings are inferred from code numbers).

## By lead time (top 10% list, gradient boosting)

Share of the churners reached inside each band of days from the cutoff to the last expiration: January 2017: 88.0% (1–7 days), 67.6% (8–14), 65.3% (15–21), 61.6% (22–31); February 2017: 81.9%, 69.4%, 64.6%, 58.7%. Users who expire soon are easier to find, and they leave the least time to act; the auto-renew rule reaches 63.5% and 61.9% in the 1–7 day band.

## Calibration

On the test months the predicted probabilities follow the observed rates: in the highest-risk decile 32.9% predicted against 32.4% observed (January) and 30.2% against 26.9% (February); the lowest deciles are slightly under-predicted (0.1% to 0.2% predicted against 0.4% to 0.5% observed). March 2017 is under-predicted (see above).

## Limits

- Evaluated on three months; the numbers differ from month to month (AUC 0.885, 0.865, 0.810), so the figures above should not be read as a stable level.
- Rebuilt labels follow the demonstration rule of the official labeller; the external month with official labels is much weaker, so the headline recall values probably overstate performance under the official definition.
- Predicted risk is not the likelihood of responding to an offer. The results say who is likely to lapse, not who can be saved.
- No intervention effect and no financial return is claimed.
- The member profile is a later snapshot (2017-11) and the two transaction releases overlap on 7,249 (user, date) keys; the overlap rule is not verified (see the model card).
- The question of how early the signals appear is only partly answered: the cutoff is the start of the month, so signals are measured 1 to 31 days before the expiration; earlier horizons were not tested.
