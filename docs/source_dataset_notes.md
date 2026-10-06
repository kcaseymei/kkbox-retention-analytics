# Source dataset notes (official description)

Source: Kaggle, WSDM – KKBox's Churn Prediction Challenge (https://www.kaggle.com/competitions/kkbox-churn-prediction-challenge). These notes paraphrase the official data description as supplied by the project owner on 2026-10-05; the Kaggle page remains the authority. Everything below is **documented**, not independently verified, unless the "Observed locally" column says otherwise. Observed values are full-data results from `notebooks/01_data_audit.ipynb` or exploratory read-only checks.

## Documented release map

| File | Documented content | Observed locally | Status |
|---|---|---|---|
| `train.csv` | Labels for users whose membership expires in **February 2017**; churn/renewal observed roughly in March 2017 | 992,931 rows; label rate 6.39% | Window not yet verified from transactions |
| `train_v2.csv` | Refreshed 2017-11-06; labels for users whose membership expires in **March 2017**; outcome roughly April 2017 | 970,960 rows; label rate 8.99% | Window not yet verified |
| `sample_submission_zero.csv` | The original test set: users whose membership expires in March 2017, with placeholder zero predictions | 970,960 users, all zero; all 970,960 are in `train_v2` (100% match, same user set) | Verified locally (full data, 2026-10-05) |
| `sample_submission_v2.csv` | Refreshed test set: users whose membership expires in **April 2017**; true labels are not public | 907,471 users, all zero placeholders | Placeholders, not labels |
| `transactions.csv` | Transactions up to 2017-02-28 | 21,547,746 rows; 2015-01-01 to 2017-02-28 | Consistent |
| `transactions_v2.csv` | Refreshed; transactions up to 2017-03-31 | 1,431,009 rows: 1,069,822 in March 2017 plus 361,187 earlier; no row identical to `transactions.csv` | Differs from a full refresh: it behaves as an increment plus 361,187 earlier rows, concentrated in January–February 2017 (to be explained) |
| `user_logs.csv` | Daily listening logs, collected up to 2017-02-28 | 392,106,543 rows; 2015-01-01 to 2017-02-28 | Consistent |
| `user_logs_v2.csv` | Refreshed; logs up to 2017-03-31 | 18,396,362 rows; **March 2017 only** | Observed content is an increment, not full history |
| `members_v3.csv` | Refreshed 2017-11-13; replaces `members.csv` with `expiration_date` removed; not every user has a member record | 6,769,473 unique `msno`; 11.33% of `train_v2` users unmatched | Consistent |
| `WSDMChurnLabeller.scala` | Official label generator; date constants edited so it runs on a laptop | Inspected, not executed | See `docs/churn_definition.md` |

The organizers state that on their cluster the log history spans 2015-01-01 to 2017-03-31, and that train/test sets and the public/private leaderboards were split by transaction date.

## Documented label definition

- Churn means the user made **no new valid subscription transaction within 30 days after the current membership expiration date**. `is_churn = 1` is churn, `0` is renewal.
- The key fields are `transaction_date`, `membership_expire_date` and `is_cancel`. Cancellation does not imply churn (a user can cancel to change plans and renew).
- A user is in scope only if the effective expiration date falls inside the target month. A later transaction that moves the expiration outside the month removes the user from that month's population.
- The supplied worked examples contain typographic year errors (`0217`, `3017`); see `docs/churn_definition.md`.

## Documented field notes

| Field | Note |
|---|---|
| `plan_list_price`, `actual_amount_paid` | New Taiwan Dollar (NTD) |
| `is_cancel` | Whether the user cancelled the membership in this transaction |
| `num_25`, `num_50`, `num_75`, `num_985`, `num_100` | Songs played in length bands: under 25%, 25–50%, 50–75%, 75–98.5%, over 98.5% of the song |
| `num_unq`, `total_secs` | Unique songs played; total seconds played |
| `bd` | Age; documented outliers from −7000 to 2015 (observed locally: −7,168 to 2,016) |
| Dates | `%Y%m%d` |

## Project implications (hypotheses until verified in local data)

- Two label windows exist: February expirations (`train`) and March expirations (`train_v2`). Their rates must not be pooled.
- Time-ordered validation (train on the February window, validate on the March window) matches the competition's own structure.
- A February-window label is probably not known at the March-window prediction time (renewal is observed up to 30 days after expiry), so it must not be used as a March-window feature unless the windows show otherwise.
- April test labels are not public; `sample_submission_v2` cannot be used for evaluation. `train_v2` is the holdout candidate.
- The organizers encourage generating additional training labels from the transaction history with the supplied labeller.

## Verification still to do

1. Reconstruct effective expiration from transactions and confirm the February and March windows for `train` and `train_v2`.
2. Explain the 361,187 pre-March rows in `transactions_v2` and the 7,249 overlapping (user, transaction date) keys with differing expiration dates.
3. Decide the treatment of `membership_expire_date` values before 2015 in `transactions.csv` (measured: 9,840 rows, of which 1,776 are 1970-01-01).
