"""Evaluation of churn scores at a limited intervention capacity.

The business question is not "how accurate is the model" (a list that predicts nobody churns is about 91%
accurate) but "if we can contact only the top K% of the expiring users, how many churners do we reach?".
For a score per user and a capacity K:

* precision@K = churners among the selected / selected
* recall@K    = churners among the selected / all churners
* lift@K      = precision@K / churn rate of the whole group (the random list reaches the base rate)

Ties are broken at random with a fixed seed, so a yes/no rule that flags more users than K picks a random
subset of the flagged users instead of an arbitrary one.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score

CAPACITIES = (0.05, 0.10, 0.20)


def select_top(score, fraction, seed=0):
    """Boolean mask of the top ``fraction`` of users by score (random tie-break)."""
    score = np.asarray(score, dtype=float)
    n = len(score)
    n_select = int(np.ceil(round(fraction * n, 9)))
    order = np.random.default_rng(seed).permutation(n)
    ranked = order[np.argsort(-score[order], kind='stable')]
    mask = np.zeros(n, dtype=bool)
    mask[ranked[:n_select]] = True
    return mask


def topk_metrics(y, score, fractions=CAPACITIES, seed=0):
    """Precision, recall, and lift at each capacity, plus the base rate; one row per capacity."""
    y = np.asarray(y, dtype=int)
    base_rate, total_churn = y.mean(), y.sum()
    rows = []
    for fraction in fractions:
        selected = select_top(score, fraction, seed)
        hits = int(y[selected].sum())
        precision = hits / selected.sum()
        rows.append({'capacity': fraction, 'selected': int(selected.sum()), 'churners_reached': hits,
                     'precision': precision, 'recall': hits / total_churn if total_churn else np.nan,
                     'lift': precision / base_rate if base_rate else np.nan, 'base_rate': base_rate})
    return pd.DataFrame(rows)


def band_metrics(y, score, band, fraction, seed=0):
    """For the global top-``fraction`` list, precision and recall inside each band (for example lead time)."""
    y, band = np.asarray(y, dtype=int), pd.Series(np.asarray(band)).reset_index(drop=True)
    selected = select_top(score, fraction, seed)
    rows = []
    for name, index in band.groupby(band, observed=True).groups.items():
        index = np.asarray(index)
        in_band = y[index]
        chosen = selected[index]
        rows.append({'band': name, 'users': len(index), 'selected': int(chosen.sum()),
                     'precision': in_band[chosen].mean() if chosen.any() else np.nan,
                     'recall': in_band[chosen].sum() / in_band.sum() if in_band.sum() else np.nan,
                     'base_rate': in_band.mean()})
    return pd.DataFrame(rows)


def auc(y, score):
    """Area under the ROC curve (NaN when only one class is present)."""
    y = np.asarray(y, dtype=int)
    return roc_auc_score(y, score) if 0 < y.sum() < len(y) else np.nan


def brier(y, probability):
    """Mean squared error of predicted probabilities (lower is better)."""
    return brier_score_loss(np.asarray(y, dtype=int), np.asarray(probability, dtype=float))


def calibration_table(y, probability, bins=10):
    """Mean predicted probability against the observed churn rate in equal-sized score bins."""
    frame = pd.DataFrame({'y': np.asarray(y, dtype=int), 'p': np.asarray(probability, dtype=float)})
    frame['bin'] = pd.qcut(frame['p'].rank(method='first'), bins, labels=False) + 1
    table = frame.groupby('bin').agg(users=('y', 'size'), mean_predicted=('p', 'mean'), observed_rate=('y', 'mean'))
    return table
