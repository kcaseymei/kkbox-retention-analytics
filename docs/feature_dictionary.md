# Feature dictionary

The model uses **57 features** in three groups, computed per user and target month at the prediction cutoff `T` (the last day of the previous month). Every feature uses only data dated on or before `T` (checked in `src/leakage_checks.py`). The feature table has 63 columns: these 57 plus `msno`, `target_month`, `cutoff`, `label_source`, `is_churn` (the label) and `has_member_profile` (a diagnostic that is not used as a feature, see below). Code: `src/behavior_features.py`, `src/subscription_features.py`; build: `src/build_features.py`.

Windows of `w` days include the cutoff day and the `w-1` days before it (for example 7 days = `T-6` to `T`).

## 1. Listening behavior: 31 features (source: user logs)

| Feature | Definition | Missing when |
|---|---|---|
| `active_days_w` (w = 7, 14, 30, 60, 90) | Number of days with a listening log in the window | No log in the last 90 days |
| `plays_w` | Total plays in the window (all completion bands summed) | No log in the last 90 days |
| `secs_w` | Total listening seconds in the window; values outside 0 to 86,400 per day are ignored (DQ-001) | No log in the last 90 days (0 if every day in the window is invalid, with the flag set) |
| `unique_songs_w` | Sum over days of the daily count of unique songs (a song played on two days counts twice) | No log in the last 90 days |
| `completed_share_w` | Plays that reached at least 98.5% of the song divided by all plays in the window | No plays in the window |
| `days_since_last_log` | Days from the last log (within the last 90 days) to `T` | No log in the last 90 days |
| `trend_days_7_vs_prior_23` | Daily rate of active days in the last 7 days minus the rate over the 23 days before | No log in the last 90 days |
| `trend_days_30_vs_prior_30` | Daily rate of active days in the last 30 days minus the rate over the 30 days before | No log in the last 90 days |
| `has_log_90` | True if the user has at least one log in the last 90 days | never |
| `no_log_90_flag` | The opposite of `has_log_90` (kept as an explicit flag) | never |
| `has_invalid_secs_90` | True if any log in the last 90 days has implausible `total_secs` | never |

That is 5 measures × 5 windows = 25, plus the 6 single features = 31. Missing listening is **not** zero listening: users without logs get missing values and the flags.

## 2. Subscription history: 20 features (source: transactions, both releases)

| Feature | Definition |
|---|---|
| `has_history` | True if the user has any transaction up to `T` (since 2015-01-01) |
| `tenure_days` | Days from the user's first transaction in the data to `T` (left-censored: the data starts on 2015-01-01) |
| `first_tx_in_first_data_month` | True if the first transaction is in January 2015, so tenure may be truncated |
| `n_transactions`, `n_cancellations` | Number of transactions, and of cancellation rows among them, up to `T` |
| `n_transactions_90`, `n_cancellations_90` | The same within the last 90 days |
| `days_since_last_transaction` | Days from the latest transaction to `T` |
| `days_to_expiration` | Days from `T` to the expiration of the user's last row (the lead time; negative if already expired) |
| `last_plan_days`, `last_list_price`, `last_amount_paid` | Plan length in days, list price, and amount paid (New Taiwan Dollar) of the last row |
| `last_auto_renew` | Auto-renew flag of the last row (1 on, 0 off) |
| `last_payment_method` | Payment method code of the last row (category; meaning unknown) |
| `last_is_cancel` | True if the last row is a cancellation |
| `last_paid_zero`, `last_paid_below_list` | True if the last payment was zero, or below the list price |
| `zero_paid_share`, `auto_renew_share` | Share of non-cancellation transactions with a zero payment, and with auto-renew on |
| `n_plan_changes` | Number of changes of plan length between consecutive non-cancellation transactions |

"Last row" follows the order of the official labeller (`src/churn_labels.py`), so it is the row that defines the user's last expiration. Users without history have missing values and `has_history = False` (only possible for the official March 2017 users).

## 3. Profile: 6 features (source: members file)

| Feature | Definition |
|---|---|
| `city`, `registered_via` | Category codes (meaning unknown); a negative code is treated as missing |
| `gender` | male, female, or unknown (missing is kept as unknown) |
| `age` | Supplied age when it lies between 1 and 100, otherwise missing |
| `age_valid` | True when the age is within 1 to 100 |
| `registration_days` | Days from the registration date to `T`; missing if the registration is after `T` |

The members file is a later snapshot (November 2017), so these attributes may have changed after `T`; the ablation shows they add no consistent gain.

## Columns that are not features

`msno` (identifier), `target_month`, `cutoff`, `label_source` (rebuilt or official), `is_churn` (the label), and `has_member_profile` (whether the member row exists: not shown to be knowable at `T`, so it is only a diagnostic).

## Categorical features

`city`, `registered_via`, `last_payment_method`, and `gender` are treated as categories by the models; all others are numeric or true/false.
