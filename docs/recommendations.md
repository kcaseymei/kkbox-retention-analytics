# Recommendations

Status: **hypotheses to test, not results.** Each recommendation states its target, evidence, mechanism, timing, feasibility, and limits. Evidence comes from `reports/model_results.md`, `reports/retention_signals.md`, and `reports/sql_analysis.md`; the test that would confirm or reject them is in [experiment_design.md](experiment_design.md). Associations in historical data do not show that an action works, and predicted risk is not the likelihood of responding to an action.

## Summary

| Priority | Action | Target | Evidence | Status |
|---|---|---|---|---|
| 1 | Renewal reminder before the expiration | The top 10% of expiring users by predicted risk | Contacting this list reaches 71.9% and 68.1% of the churners (January, February 2017) against 52.5% and 54.2% for the best rule | Hypothesis, to test |
| 2 | Prompt to turn on auto-renew | Manual renewers (auto-renew off on the last transaction) | 12% to 18% of the users but 63% to 87% of the churners from mid-2016 on; churn rate 20% to 45% against 1.4% to 3.5% | Hypothesis, to test |
| 3 | Outreach after a drop in listening | Users whose listening days fell by more than 25% | Churn about 1.5 times that of stable users (median of 21 months); adds about 1 point of recall to the model | Lower priority, to test only after 1 and 2 |

## 1. Renewal reminder for the highest-risk users

- **Target.** The 10% of the month's expiring users with the highest predicted risk, identified on the last day of the previous month.
- **Evidence.** On the held-out months January and February 2017 the list reaches 71.9% and 68.1% of the churners; the precision of the list is 32.4% and 26.9% (lift 7.2 and 6.8). With the official labels the lead over the "no auto-renew" rule is smaller (60.8% against 52.6% in February) and in March 2017 it disappears at 10% capacity, so the ranking is useful but the size of its advantage depends on the label definition.
- **Mechanism (hypothesis).** Some of these users let the subscription lapse through inattention or a payment problem; a timely reminder or a payment fix converts a share of them. The data cannot show how large that share is.
- **Timing.** At the start of the expiry month; the lead time to the expiration is 1 to 31 days, and users with fewer than 3 days left get little time to respond (reported as a separate band).
- **Feasibility.** The list is produced by the repository's pipeline (feature tables, model, purge rule) and needs a monthly refresh; the reminder itself needs a channel (email or in-app) that the service has.
- **Risks.** Message fatigue and complaints (guardrails in the design); the model weakens in later months, so the list must be rebuilt each month; users who would have renewed anyway receive the message (the control arm measures this).

## 2. Prompt to turn on auto-renew for manual renewers

- **Target.** Users whose last transaction has auto-renew off. They are about 12% to 18% of each month's users.
- **Evidence.** From July 2016 to February 2017 they account for 63.3% to 87.5% of the churners (a single month, November 2016, reaches 87.5%) and churn at 20% to 45% against 1.4% to 3.5% for auto-renewers. In July 2015 to June 2016 the concentration was lower (30.5% to 57.5% of the churners), so the figure belongs to the later period. Auto-renew status, and the payment method code that largely encodes it, is the strongest signal in the models.
- **Mechanism (hypothesis).** Turning on auto-renew removes the renewal decision, so the subscription continues unless the user cancels. Manual renewers may differ from auto-renewers in ways the prompt cannot change (price sensitivity, intent to leave), so the observed gap is not the effect of the prompt.
- **Timing.** Together with the reminder, before the expiration; a prompt at the moment of payment may also work and is outside this design.
- **Feasibility.** Requires the service to support a one-step auto-renew prompt in its flow, which the data does not show.
- **Risks.** Users who turn on auto-renew and later notice an unwanted charge may cancel, complain, or request refunds (guardrails); the experiment compares the prompt with the reminder alone.

## 3. Outreach after a drop in listening (lower priority)

- **Target.** Users whose listening days in the last 30 days fell by more than 25% against the 30 days before.
- **Evidence.** They churn about 1.5 times as often as stable users (median over 21 months, range 0.99 to 2.23), and the signal holds within auto-renewers and within manual renewers; but users whose listening **increased** also churn more than stable users, and listening features add only about 1 point of recall at 10% capacity on top of the subscription record.
- **Recommendation.** Do not build a separate campaign yet. Use the signal as an additional input of the risk score and revisit after the first experiment.

## What not to conclude

- The model ranks users by risk; it does not identify who responds to an action. The first experiment estimates the effect by risk band to find out.
- No retention lift, revenue, or cost saving is claimed. The scenario in `experiment_design.md` shows how a break-even is computed from assumed values and is not a forecast.
- The data are 2017 records of one service; behavior and prices today may differ.

## Sequencing

1. Recompute the baseline renewal rate and run an A/A check on the latest complete month.
2. Run the experiment of `experiment_design.md` on two monthly cohorts: reminder against control in all risk bands; reminder plus auto-renew prompt against reminder among manual renewers.
3. Read the primary outcome 30 days after the last expiration of each cohort; apply the decision rules of the design.
4. Only then consider a listening-based campaign or a retrained model.

## Limits

The evidence is observational, label definitions affect the size of the model's advantage, and the economics rest on assumed prices and costs. These recommendations become findings only if the experiment supports them.
