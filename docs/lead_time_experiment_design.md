# Lead-time experiment: how early does churn become predictable?

Status: **draft, not implemented, not approved.** Nothing below is a result. Items marked *hypothesis* are unverified. Builds on `docs/prediction_design.md` (cutoffs, purge rule, splits) and stage E (`reports/model_results.md`).

## 1. Question

Headline question, part 3: how early before expiration do signals become usable, and what can a model reach at each horizon compared with simple rules, at a fixed capacity K?

## 2. Terms (two meanings of "window" must not be mixed)

| Term | Meaning | In this experiment |
|---|---|---|
| Horizon h | Days by which the prediction cutoff is moved back from the stage E cutoff T (the last day before the target month) | **The variable we change.** T_h = T - h |
| Feature lookback | How far back the feature windows reach from the cutoff (7/14/30/60/90 days, as in the feature table) | **Held fixed** at the existing definitions |
| Native lead time | Days from T to the user's expiration (1–31, already a feature and an evaluation band) | Reported as a band, not changed |

So "180-day window" means a cutoff 180 days before T, not a 180-day lookback. Effective distance to expiration at T_h is h + native lead time.

## 3. Design

- **Rows and labels fixed across horizons:** same users, same target months, same rebuilt labels. Only the cutoff of the features changes. This makes the curves comparable (any change comes from the information, not from a different population).
- **Test months:** 2017-01 and 2017-02 (rebuilt labels). 2017-03 (official labels) as a separate external check, as in stage E.
- **Horizons:** h = 0 (stage E result, reproduced as a sanity check), 7, 14, 30, 60, 90, 180. Seven points, not nine; add 21 or 120 only if the curve has a bend worth resolving.
- **Features at T_h:** the existing 63-column table recomputed with cutoff T_h (listening, subscription, profile families). Each family is also run separately for h in {30, 90} to see which family carries the signal. *Open: confirm that `behavior_features` and `subscription_features` take the cutoff as a parameter; if the cutoff is hard-wired to month ends, h must be rounded to month ends (30/60/90/180) or the builders must be generalized, with tests.*
- **Models and references (per horizon):** gradient boosting (scikit-learn `HistGradientBoostingClassifier`, as in stage E), logistic regression, the auto-renew rule, a random list. Report the model's gain **over the auto-renew rule**, not only its own curve, because the rule already captures about 64% of the February 2017 churners (see master plan).
- **Metric:** recall at K = 10% (primary), 5% and 20% (secondary), with lift over random and a month-level spread across the two test months. Calibration only at h = 0 and the horizon where the curve flattens.
- **Training months per horizon:** expanding window with the purge rule adapted to T_h (section 4).

## 4. Leakage and validity controls

1. **Purge rule at T_h.** A training month's last day + 30 days must not be later than T_h (`leakage_checks.check_purge` with the shifted cutoff). For h = 180 the training months end about six months earlier than in stage E, so the training set is smaller; this confounds "less information" with "less and older training data". Mitigation: also run each horizon with the training months fixed to those valid for h = 180 (the same data for all horizons), and compare the two curves.
2. **Population selection uses T-time information.** The users of target month M are those whose *last* expiration lies in M, a fact known only at T (a user may renew early or change plan between T_h and T). Keeping the population fixed (section 3) is clean for comparison but is optimistic as an operational claim: at T_h the business would not yet know exactly who expires in M. State this limitation in the results. *Hypothesis:* the optimistic bias grows with h. Optional check: define the population at T_h as users whose current expiration at T_h lies in M and compare.
3. **Features dated on or before T_h only.** Rerun the four existing leakage checks at each horizon; add an assertion that the maximum source date entering any feature is ≤ T_h.
4. **Current-subscription features** (days to expiration, latest auto-renew flag, cancel history) at T_h describe the subscription before later renewals/changes; their value for churn may fall with h simply because the state is stale. This is a finding, not a defect, but must be explained next to the curve.
5. **Batch cohorts** (for example 2015-04-30) are outside the test months; no special handling needed.
6. **No tuning on test months.** Hyperparameters fixed from stage E or tuned on validation months 2016-07 to 2016-12 only.

## 5. Outputs

- `reports/lead_time_results.md`: table (horizon × model/rule × recall@K), a chart of recall@10% against h with the auto-renew rule and random lines, a second chart of the model's gain over the rule, family ablation at h = 30 and 90, and the sensitivity check of section 4.1.
- Short answer to the headline question in one sentence, with the caveats of section 4.2.
- Update `docs/prediction_design.md` (horizon definition) and the master plan after approval and execution.

## 6. Expected outcomes and how to read them (*hypotheses*)

- Recall declines with h, steeply at first as the subscription state goes stale; listening features may hold up better than the subscription state, which would be the interesting finding.
- If the model's gain over the auto-renew rule is about zero at every h, the honest conclusion is that listening data adds little lead time on this dataset (consistent with the +1 point seen in the ablation).
- If everything collapses to random by h = 60, the answer to "how early" is "weeks, not months".

## 7. Dependencies and order of work

1. Resolve the March 2017 / early-renewer labeling questions first (master plan, next action), since they affect the external check.
2. Check whether the feature builders accept an arbitrary cutoff; generalize with tests if not.
3. Run h = 0 and reproduce the stage E numbers exactly (acceptance test for the pipeline).
4. Run the other horizons; write the report.

Estimated effort: 2–3 days, dominated by recomputing features per horizon (log scans over the Parquet user logs).
