# kkbox-retention-analytics
End-to-end subscription retention analysis using SQL and Python to identify churn drivers, behavioral patterns, and actionable retention opportunities.

## Churn Definition

This project follows the subscription-based churn definition from the
[WSDM – KKBox Churn Prediction Challenge](https://www.kaggle.com/competitions/kkbox-churn-prediction-challenge/data).
A subscriber is churned when no qualifying renewal occurs within the 30-day
renewal window relative to their **effective membership expiration**. The official
labeller uses a gap of **less than 30 days** for retention; exactly 30 days or more
counts as churn.

Effective expiration is reconstructed from ordered transaction history, including
cancellations and plan changes that can shorten or extend membership.
**`is_cancel = 1` does not automatically mean churn**: a subscriber can cancel a
plan and renew within the allowed window. Users whose effective expiration at the
history cutoff lies outside the target expiration window are excluded from that
prediction population.

The competition-provided `WSDMChurnLabeller.scala` is the official reproducibility
aid for reconstructing expiration, selecting eligible users, and generating churn
labels from subsequent renewal behavior. Its demonstration dates must be aligned
with the selected data release before reproducing labels.
See [Churn Definition and Label Reconstruction](docs/churn_definition.md) for
implementation details, transaction examples, leakage controls, and the planned
validation against `train_v2.is_churn`.
