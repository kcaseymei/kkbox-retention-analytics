# Experiment design: renewal reminders and auto-renew prompts

Status: **design, not run.** Nothing here is a result and no effect is claimed. Items marked **[A]** are assumptions chosen as defaults for this case study; each is stated so it can be replaced with the real value. Historical figures come from `reports/model_results.md`, `reports/retention_signals.md`, and the feature tables. Recommendations that motivate the test: [recommendations.md](recommendations.md).

## 1. Questions and hypotheses

- **H1 (reminder).** Sending a renewal reminder to expiring subscribers ranked highest by predicted risk raises the share who still have a paid subscription 30 days after their expiration date.
- **H2 (auto-renew prompt).** For manual renewers (last transaction with auto-renew off), adding a prompt to turn on auto-renew raises that share more than the reminder alone.
- **Question the test must answer that the model cannot:** predicted risk is not the likelihood of responding. The design therefore also estimates the effect **by risk band**, to see whether the users the model ranks highest are the ones whose renewal can be changed.

## 2. Population

- **Eligible:** subscribers whose last subscription expires in the target month, identified at the cutoff (the last day of the previous month) with the pipeline of this repository.
- **Excluded:** users who already renewed before the cutoff, users flagged in the service's do-not-contact list, and users with fewer than 3 days between the contact and the expiration (reported separately, see section 5).
- **Risk score:** the gradient boosting model of stage E, trained only on months whose labels are complete at the cutoff (the purge rule).
- **Scale [A]:** in a month like February 2017 there are about 880,000 eligible users, so contacting the top 10% means about **88,000** contacts.

## 3. Randomization and arms

- **Unit:** the user. Each user is assigned once, at the first month in which they are eligible, and keeps the assignment if they appear again (this prevents a control user from being contacted later and a treated user from being re-randomized).
- **Stratification:** by risk band and by lead-time band (1-7, 8-14, 15-21, 22-31 days), with a fixed seed recorded in the protocol.
- **Risk bands:** top 10% (the list a team could afford), next 20% (10-30%), the remaining 70%. Within each band users are randomized, so the effect can be compared across bands; the lower bands are sampled (treat a random 10% of the band) to keep the number of contacts small.
- **Arms:**

| Arm | Who | What |
|---|---|---|
| Control | Randomized users in every band | No contact (the normal renewal flow) |
| Reminder | Randomized users in every band | A renewal reminder at the start of the expiry month |
| Reminder + auto-renew prompt | Manual renewers only | The reminder plus a one-step prompt to turn on auto-renew |

- Control share **[A]**: 50% of the users eligible for contact in the top band, 50% in the sampled lower bands.

## 4. Outcomes

- **Primary:** the user has an **active paid subscription 30 days after the original expiration date** (renewal on or before that day, including early renewals). This is defined directly on the subscription state, so it does not depend on how a label file treats early renewals (see `docs/churn_definition.md`).
- **Secondary:** auto-renew turned on before the expiration (H2); renewal by the expiration date; revenue per eligible user over 60 days.
- **Subgroups (pre-specified):** risk band, lead-time band, manual against auto-renewer, plan length.

## 5. Guardrails

- Unsubscribe rate from messages, complaint or support-ticket rate, and cancellation rate among contacted users, each compared with control.
- **Cost per retained subscriber** against the break-even in section 7.
- **Stop rule [A]:** pause the arm if the unsubscribe or complaint rate in the treatment arm exceeds the control rate by more than 1 percentage point.
- Users with less than 3 days between the contact and the expiration get little time to act: they are analyzed as a separate lead-time band and not pooled into the primary estimate.

## 6. Sample size

Two-sided test, significance level 0.05, power 80% **[A]**, minimum detectable effect **+2 percentage points [A]**. Users per arm for a two-proportion comparison (normal approximation):

| Baseline renewal rate | +1 pt | +2 pt | +3 pt |
|---|---|---|---|
| 60% | 37,513 | 9,336 | 4,129 |
| 73% | 30,575 | **7,550** | 3,313 |
| 80% | 24,641 | 6,039 | 2,629 |

- **Baseline [A]:** 73% is the renewal rate in the top 10% of February 2017 (churn label rate 26.9% in that list); January was 67.6% and the official March 2017 file 59.6%, so the baseline moves from month to month and the sample size should be recomputed from the latest month before the test.
- With power 90% the 73% / +2 pt cell becomes 10,107 per arm.
- Add a 10% buffer for undelivered messages, giving about **8,300 users per arm** in the top band. The top band alone (88,000 contacts) is enough for one month; the test should still cover **two monthly cohorts** to check that the result is stable.
- Two confirmatory comparisons (H1, H2): use the Holm correction. Subgroup results are exploratory.
- **Timing:** contact at the start of the expiry month; the outcome is complete 30 days after the last expiration of that month, so the readout is about two months after the contact.

## 7. Break-even and an illustrative scenario (assumptions, not a result)

- Value of one retained subscriber-month **[A]**: NT$149, the most common list price among manual renewers (the list price is NT$99 for 45% and NT$149 for 40% of 30-day plans in February 2017).
- Cost per contact **[A]**: NT$1 for a message.
- **Break-even effect** = cost / value = 1 / 149 = **0.67 percentage points**; the +2 point design effect is about three times that.
- Scenario for a month like February 2017: 87,954 contacts cost about NT$88,000; an effect of +2 points would retain about 1,760 subscribers, worth about NT$262,000 for one more month, a net of about NT$174,000 before any later months. This only shows how the numbers combine under the stated assumptions.

## 8. Analysis plan (fixed before the test)

1. Intention to treat: compare the primary outcome between each treatment arm and control within strata, report the difference in proportions with a 95% confidence interval.
2. Check balance on the pre-treatment features and the sample ratio (a mismatch between the planned and the observed arm sizes is a data problem to fix before any effect is read).
3. Estimate the effect by risk band; report whether the effect grows, stays flat, or falls with predicted risk.
4. Report guardrails and the cost per retained subscriber with its interval.
5. No interim peeking at the primary outcome; guardrails may be monitored.

## 9. Threats to validity

- **Shared accounts and repeat entries:** one assignment per user; contamination between users is possible and unmeasured.
- **Outcome definition:** early renewals count as renewal; a reminder could simply move a renewal earlier, which the 60-day revenue outcome helps detect.
- **Seasonality and batch cohorts:** some months have unusual expiry batches (for example 30 April 2015 and the spike of March 2016); test months are chosen without them and the strata include the expiry date.
- **Model drift:** the model performed worse in later months (AUC 0.885, 0.865, 0.810); the risk bands should be recomputed with the latest data.
- **External validity:** the data is a 2017 snapshot of one service.

## 10. Decision rules

- **Roll out the reminder** if the primary effect is at least the break-even (0.67 points) with the lower end of the confidence interval above 0, and no guardrail is breached.
- **Roll out the auto-renew prompt** only if it beats the reminder alone among manual renewers by the same rule.
- **Narrow or drop** the action for bands where the effect is not distinguishable from zero.

## 11. What can be checked before spending anything

- An **A/A test** on historical data: split a past month's top list at random and confirm the primary outcome shows no difference (a check of the pipeline, not of an intervention).
- Recompute the baseline renewal rate and the sample sizes for the latest complete month.

## 12. Limits

The defaults in this document are assumptions, the effect sizes are targets rather than expectations, and nothing here shows that contacting users retains anyone. The result of the experiment, not this design, would be the evidence.
