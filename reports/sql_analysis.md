# SQL analysis in PostgreSQL (first block)

Date: 2026-10-07
Evidence: **full-data** results from the typed tables in `analytics` (see [data model](../docs/data_model.md)); each query is in `sql/analysis/` and was run in PostgreSQL 18. Descriptive only; no causal claims.

## 1. One user's subscription history — `01_user_subscription_history.sql`

A user with 12 transactions (release v1; identifier not shown): every row is a 30-day plan renewed on the 15th of each month from 2016-03-15 to 2017-02-15, and each expiration date moves forward by one plan length (2016-04-15 to 2017-03-15). This confirms the grain (one row per transaction) and the "expiration moves forward on renewal" logic that the churn label relies on.

## 2. Users with any expiration per month — `02_expiring_users_by_month.sql`

Distinct users with any transaction expiring in the month, both releases: from 412,086 (2015-02) to 993,531 (2017-02), peaking at 1,126,251 in 2016-11. These are larger than the churn cohorts (for February 2017, 993,531 against 879,537 users) because this counts **any** expiration, not only each user's last one.

## 3. Last-expiration population for February 2017 — `03_last_expiration_population.sql`

At the 2017-01-31 cutoff, 883,727 users have their last expiration in February 2017 under the simplified SQL ordering (latest transaction date, then latest expiration). The Python rebuild with the full labeller ordering (`src/churn_labels.py`) finds 879,537, a difference of 4,190 users (0.48%). The gap is attributable to ordering details (plan signature, cancellations) — a *hypothesis* not yet isolated; the two engines agree to within half a percent.

## 4. Official churn label rate and profile coverage — `04_official_label_churn.sql`

| Release | Target month | Users | Churn label rate | Users without a member profile |
|---|---|---|---|---|
| v1 | 2017-02 | 992,931 | 6.39% | 11.66% |
| v2 | 2017-03 | 970,960 | 8.99% | 11.33% |

The rates match the audit (6.39% and 8.99%). Rates describe the labeled populations, not platform churn.

## 5. Plan mix and auto-renew (transactions, release v1) — `05_plan_mix.sql`

| Plan length | Transactions | Share | Auto-renew on |
|---|---|---|---|
| 30 days | 18,956,290 | 87.97% | 88.53% |
| Over 30 days | 1,093,337 | 5.07% | 70.12% |
| 0 days | 870,124 | 4.04% | 93.09% |
| Under 30 days | 627,995 | 2.91% | 0.00% |

Shares are of transactions, not users. The 0-day group matches the audit count (870,124); a 0-day plan does not mean zero payment (DQ-011). Plans under 30 days never have auto-renew on. Whether plan length relates to churn is not tested here.

## 6. Monthly churn — `06_monthly_churn.sql` (runs about 3 minutes)

Rule: cutoff = last day of the previous month; population = users whose last expiration at the cutoff lies in the target month; churn = no later transaction, or the next one 30 or more days after the expiration. This is a **simplified SQL version** (non-cancel transactions only, one `lead()` pass); it is not identical to the Python rebuild, so rates differ slightly (February 2017: 888,374 users and 4.45% here, 879,537 and 3.95% in Python), and neither equals the official 6.39%. Use it for the shape over time.

| Month | Users | Churn | Month | Users | Churn |
|---|---|---|---|---|---|
| 2015-07 | 501,876 | 6.11% | 2016-05 | 744,466 | 7.34% |
| 2015-08 | 541,922 | 6.80% | 2016-06 | 748,511 | 6.05% |
| 2015-09 | 576,483 | 11.00% | 2016-07 | 772,026 | 5.83% |
| 2015-10 | 590,324 | 9.49% | 2016-08 | 805,708 | 4.58% |
| 2015-11 | 685,693 | 7.86% | 2016-09 | 852,096 | 6.69% |
| 2015-12 | 746,030 | 9.80% | 2016-10 | 843,773 | 4.29% |
| 2016-01 | 770,742 | 11.31% | 2016-11 | 898,760 | 9.38% |
| 2016-02 | 705,641 | 8.71% | 2016-12 | 890,880 | 8.49% |
| 2016-03 | 818,238 | **18.53%** | 2017-01 | 876,352 | 4.93% |
| 2016-04 | 738,914 | 7.64% | 2017-02 | 888,374 | 4.45% |

Churn swings from 4.29% to 18.53%; March 2016 is the largest spike. The cause is not investigated here (the batch-expiration cohorts of notebook 02 are a candidate, a *hypothesis*).

## 7. Cohort retention — `07_cohort_retention.sql` (runs about 5 minutes)

Cohort = month of the user's first non-cancel transaction in the data; value = share with an active subscription at the end of month C+k (cohorts 2016-01 to 2016-06).

| Cohort | Users | M0 | M1 | M2 | M3 | M4 | M5 | M6 |
|---|---|---|---|---|---|---|---|---|
| 2016-01 | 88,107 | 99.2 | 77.2 | 64.2 | 62.5 | 61.6 | 61.9 | 66.7 |
| 2016-02 | 72,019 | 98.0 | 70.9 | 66.2 | 64.1 | 63.0 | 65.8 | 64.5 |
| 2016-03 | 59,807 | 98.0 | 71.2 | 62.3 | 60.0 | 64.8 | 64.6 | 62.2 |
| 2016-04 | 38,521 | 99.7 | 61.7 | 53.9 | 56.0 | 55.2 | 54.5 | 53.0 |
| 2016-05 | 42,773 | 98.1 | 70.5 | 67.4 | 66.2 | 64.6 | 64.1 | 61.8 |
| 2016-06 | 53,514 | 96.4 | 63.2 | 60.6 | 58.9 | 58.7 | 57.6 | 54.9 |

The largest drop is between M0 and M1 (about 20–35 points); afterwards retention levels off near 55–66%. Limits: the data starts on 2015-01-01, so a "first transaction" can be a returning user, not a new subscriber; shares can rise again when lapsed users return (for example 2016-01 at M6). Whether the M0–M1 drop is a trial or one-month-plan effect is a *hypothesis* (plan type not split here).

## 8. Renewal gap — `08_renewal_gap.sql` (runs seconds)

Gap = date of the next non-cancel transaction minus the expiration date, for 18.7 million expirations dated 2015-02-01 to 2017-01-31 (at least 59 days of follow-up; shares are of expirations, not users).

| Gap | Expirations | Share |
|---|---|---|
| Early (before expiry) | 4,429,806 | 23.73% |
| On the expiry day | 9,088,953 | 48.69% |
| 1–7 days | 3,016,042 | 16.16% |
| 8–14 days | 188,341 | 1.01% |
| 15–29 days | 188,636 | 1.01% |
| 30 or more days (churn under the rule) | 615,500 | 3.30% |
| No later transaction (churn under the rule) | 1,139,097 | 6.10% |

Renewal is concentrated at the expiry day and the week after (88.6% together with early renewals); only 2.0% renew 8–29 days late, and 9.4% of expirations end as churn under the 30-day rule. The sparse middle band means the 30-day threshold separates quick renewers from lapsed users rather than cutting through a dense group, so results should not be very sensitive to it (to be tested). Early renewals (23.7%) are the group the official labels treat differently (open question).

## 9. Cohort retention by first plan length — `09_cohort_retention_by_plan.sql` (runs about 4 minutes)

Cohorts 2016-01 to 2016-06 pooled (354,741 users), split by the plan length of the first non-cancel transaction; active at the end of month C+k.

| First plan | Users | M0 | M1 | M2 | M3 | M4 | M5 | M6 |
|---|---|---|---|---|---|---|---|---|
| 30 days | 302,773 | 100.0 | 70.6 | 62.2 | 61.1 | 61.2 | 61.7 | 62.4 |
| Over 30 days | 33,722 | 99.8 | 99.7 | 99.3 | 94.0 | 92.6 | 92.4 | 82.8 |
| Under 30 days | 18,246 | 66.2 | 10.8 | 9.8 | 9.6 | 10.8 | 10.4 | 10.0 |

The month 0 to 1 drop seen in section 7 comes from the 30-day plans (85% of these users, 100% to 70.6%): longer plans keep almost everyone for months, and short plans mostly do not renew (about 10% still active). Plan length of the first transaction is a strong candidate feature, and the pooled curve in section 7 mixes very different groups. This is descriptive; plan choice may reflect user type, not cause retention. Caveat as in section 7: a first transaction may be a returning user.
