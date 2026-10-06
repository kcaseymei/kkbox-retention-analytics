# Churn Definition and Label Reconstruction

## Purpose and sources

This project follows the subscription-based target in [WSDM – KKBox's Churn Prediction Challenge](https://www.kaggle.com/competitions/kkbox-churn-prediction-challenge/data). The competition's Data Extraction Details and the supplied `WSDMChurnLabeller.scala` are the reference sources. The Scala attachment was inspected directly; it has not been executed or ported as part of this documentation change.

The organizer supplied this Spark/Scala program as an official reproducibility aid for generating churn labels, including additional historical training cohorts. It reconstructs effective membership expiration from transactions, selects eligible subscribers for a target expiration window, and examines subsequent transactions for renewal. It is a label generator, not a predictive model. The competition description says the published date constants were adapted for laptop use; they must not be assumed to match the local train/test release.

## Business definition and exact boundary

A subscriber churns when there is no qualifying renewal within the 30-day grace window relative to effective membership expiration. Effective expiration reflects transaction ordering, including plan changes and cancellations; it is not simply the maximum recorded expiration date. `is_cancel = 1` does **not** automatically mean churn.

The supplied implementation defines a qualifying renewal by **`gap < 30`**, where `gap` is the integer calendar-day difference between effective expiration and the first subsequent non-cancellation transaction examined after the history cutoff. A gap of exactly 30 days is churn, as is a longer gap. Negative gaps (early renewals) also satisfy `< 30`.

Here, “valid renewal” describes the script's non-cancellation transaction and gap rule. The script does not additionally require a positive payment, a particular plan length, or a new expiration later than the previous expiration. Adding such filters would change the reference logic.

## Inputs, configuration, and output

The script reads a transaction CSV with a header and groups records by `msno`. Its transaction structs contain `payment_method_id`, `payment_plan_days`, `plan_list_price`, `transaction_date`, `membership_expire_date`, and `is_cancel`. CSV values are read as strings, with dates expected in `yyyyMMdd` format.

| Setting | Supplied script |
|---|---|
| History interval | 2017-01-01 through 2017-01-31, inclusive |
| History cutoff | 2017-01-31 |
| Candidate expiration window | 2017-02-01 through 2017-02-28, inclusive |
| Outcome transactions | All loaded transactions after 2017-01-31 |
| Execution | Spark with `.master("local")` |
| Output | Headered Spark CSV directory `sample_user_label`, with `msno` and Boolean `is_churn` |

The input path is hard-coded to the original author's machine and must be configured before running elsewhere. `repartition(1)` requests one data partition; Spark writes an output directory, not a specifically named single CSV file. Boolean `true` corresponds to churn (`1`), and `false` to retained (`0`).

The script does not establish adequate future coverage itself. Its absence-of-renewal result is trustworthy only when the input covers the required outcome horizon. Local file versions, history coverage, and train/test windows still require reconciliation before label reproduction.

## Exact logic flow

1. **Split history and future transactions.** Keep history within the configured inclusive interval and future transactions strictly after the history cutoff. Users without a transaction in that history interval never enter the candidate set.
2. **Reconstruct historical expiration with `calculateLastday`.** Sort each user's history using the comparator below and select the last row's `membership_expire_date` as `last_expire`. This respects later transaction states rather than taking a maximum across expirations.
3. **Select the analytical population.** Keep only users whose historical `last_expire` falls inside the inclusive target expiration window. Users outside it are excluded, not assigned a retained label.
4. **Join candidates to future transactions.** Use a left join on `msno`. Rows with null `payment_method_id` enter the no-activity branch and receive churn. This is the implementation's proxy for an unmatched future transaction; missing payment-method values therefore need auditing before reuse.
5. **Evaluate `calculateRenewalGap`.** Sort future records with the same comparator. Start with the historical expiration and a sentinel gap of `9999`. Before the first non-cancellation record, a cancellation moves expiration earlier only if its expiration precedes the current value. At the first non-cancellation record, compute `DAYS.between(currentExpiration, transactionDate)` and stop updating the gap. Despite the source comment referring to “after expiration,” the scan includes all transactions after the history cutoff, including early renewals before expiration.
6. **Assign labels.** A gap below 30 produces `false`; a gap of 30 or more produces `true`. If all future records are cancellations, the sentinel remains `9999`, so the result is churn. No future activity also produces churn.
7. **Export candidate labels.** Union retained, late/no-renewal, and no-activity results and write the CSV output.

Candidate membership is fixed at step 3. Future cancellations can shorten the date used to measure the renewal gap, but the supplied program does not re-run the candidate-window filter afterward. Likewise, it stops at the first non-cancellation transaction rather than simulating every later subscription cycle.

### Same-day ordering

Both functions use the following ordering:

- Transaction date ascending.
- For different plan signatures on the same day, signature descending. The signature is the raw string concatenation `plan_list_price + payment_plan_days + payment_method_id`, with no separator; it is a lexicographic comparison, not a numeric tuple comparison.
- For the same date/signature, subscriptions (`"0"`) precede cancellations (`"1"`).
- Among subscriptions with the same date/signature, expiration ascending, so the longest expiration comes last.
- Among cancellations with the same date/signature, expiration descending, so the earliest expiration comes last.

A faithful port must preserve these rules. Sorting only by date, taking the maximum expiration, or interpreting the concatenated signature as a numeric tuple can change results.

## Three competition transaction examples

These are illustrative sequences from the competition description, not observations from the local dataset. Dates are displayed as ISO dates for readability. The supplied prose contains years `0217` and `3017`; the tables normalize those obvious illustrative typos to `2017`. That normalization is not a rule for silently repairing raw data.

### Case 1 — Renewal too late: churn

| Transaction date | Membership expiration | is_cancel |
|---|---|---|
| 2017-01-01 | 2017-02-28 | false |
| 2017-02-25 | 2017-03-15 | false |
| 2017-04-30 | 2017-05-20 | false |

The relevant expiration is March 15, within the illustrative March target window. The April 30 subscription is **46 calendar days** later, beyond the grace window, so the user churns (`1`). The source's wording about “30 days away” should not be read as the exact date difference.

### Case 2 — Cancellation followed by timely renewal: retained

| Transaction date | Membership expiration | is_cancel |
|---|---|---|
| 2017-01-01 | 2017-02-28 | false |
| 2017-02-25 | 2017-04-03 | false |
| 2017-03-15 | 2017-03-16 | true |
| 2017-04-01 | 2017-06-30 | false |

The March 15 cancellation shortens expiration from April 3 to March 16. Renewal on April 1 is **16 calendar days** after March 16, satisfying `< 30`, so the user is retained (`0`). The source prose says 15 days; Java's calendar-day difference is 16. Either value yields the same label. This illustrates why cancellation alone is not churn.

### Case 3 — Effective expiration outside the target: excluded

| Transaction date | Membership expiration | is_cancel |
|---|---|---|
| 2017-01-01 | 2017-02-28 | false |
| 2017-02-25 | 2017-04-03 | false |
| 2017-03-15 | 2017-03-16 | true |
| 2017-03-18 | 2017-04-02 | false |

The later subscription changes effective expiration to April 2. For the description's March 1–31 target window, this user is outside the prediction population. The intermediate March 16 expiration does not establish eligibility when the March 18 transaction is part of the history used for selection.

**Window alignment matters:** these narrative examples illustrate a March expiration population, whereas the distributed script selects February expirations from January history. To interpret all three with a March target, a history cutoff of March 31 includes the March cancellation and plan-change records, while April renewals remain outcomes. This is an illustrative configuration, not a verified production or local `train_v2` cutoff. With a February 28 cutoff, Cases 2 and 3 would initially have April 3 expiration and would not enter a March candidate set. Do not use the examples to infer that the script dynamically reselects candidates from future outcomes.

## Analytical population and leakage implications

Report churn among **eligible, observable subscribers for a specified cutoff/window**. The denominator is not all members, all transactions, or every subscriber with any expiration in the month. Report excluded users and missing-history users separately; neither group is automatically retained. The `train_v2` label rate is a rate within its labeled population, not an established whole-platform churn rate.

Keep feature history and outcome evidence separate. Renewal transactions and cancellation adjustments after the prediction cutoff may be required to construct the label, but must not appear in prediction-time features. A full-history “latest expiration,” future cancellation flag, or future listening aggregate can leak the answer. Eligibility used for a real prediction must also be computable at its stated cutoff; retrospective examples do not justify using unavailable future history for selection.

Specify the history interval, prediction cutoff, target expiration interval, and available follow-up end for every cohort. If follow-up is incomplete, no observed renewal may mean right-censoring rather than churn; flag or exclude such cases until the outcome is observable. Keep same-day transaction records unless an audited deduplication policy preserves the reference ordering. Separate temporal cohorts when evaluating generalization and investigate member overlap in context rather than treating overlap alone as proof of leakage.

## Validation against `train_v2.is_churn` — planned

Before claiming reconstruction, align the transaction release, history start/cutoff, expiration window, and full renewal follow-up with the supplied training labels. The demonstration constants alone do not prove alignment.

Join reconstructed labels to `train_v2` by `msno`, checking uniqueness and reporting both population coverage and users present on only one side. Normalize Boolean labels to `0/1`, then report agreement, a confusion matrix, and mismatch counts on the matched, observable population. Inspect mismatches by cancellation/plan-change history, same-day ordering, gap boundaries (29/30/31 days), early renewal, no activity, cancellation-only futures, invalid dates, and missing history/follow-up. Record any deliberate departure from the Scala code.

Current status: source-code inspection and documentation only. No Spark execution, reconstructed-label comparison, agreement rate, or claim of reproducing `train_v2.is_churn` has been made.
