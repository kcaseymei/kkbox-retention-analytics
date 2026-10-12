"""Models and rules that score churn risk from the feature tables (`src/build_features.py`).

Scores: three one-feature rules (the baselines to beat), a logistic regression (standardized, with missing
indicators), and a gradient boosting model. Training uses a random sample of users per month so that
about 18 months fit in memory; evaluation always uses every user of the evaluated month.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.build_features import OUT_DIR

LABEL = 'is_churn'
# Not features: identifiers, the label, and `has_member_profile` (not shown to be knowable at the cutoff).
NOT_FEATURES = ['msno', 'target_month', 'cutoff', 'label_source', LABEL, 'has_member_profile']
CATEGORICAL = ['city', 'registered_via', 'last_payment_method', 'gender']
# Profile columns come from a later members snapshot; the model variants without them test how much they matter.
PROFILE_COLUMNS = ['city', 'registered_via', 'gender', 'age', 'age_valid', 'registration_days']
GENDER_CODES = {'female': 0, 'male': 1, 'unknown': 2}
LEAD_BANDS = [0, 7, 14, 21, 31]
LEAD_LABELS = ['1-7', '8-14', '15-21', '22-31']
# Counts, durations, and amounts: heavy right tails, so the logistic regression uses log(1 + x).
_LOG_PREFIXES = ('plays_', 'secs_', 'unique_songs_', 'active_days_')
_LOG_NAMES = ('n_transactions', 'n_transactions_90', 'n_cancellations', 'n_cancellations_90', 'tenure_days',
              'days_since_last_log', 'days_since_last_transaction', 'days_to_expiration', 'last_list_price',
              'last_amount_paid', 'registration_days', 'age', 'n_plan_changes')


def month_columns(table_columns):
    """Feature columns of a feature table (everything except identifiers, the label, and diagnostics)."""
    return [c for c in table_columns if c not in NOT_FEATURES]


def load_month(month, columns=None):
    return pd.read_parquet(OUT_DIR / f'features_{month}.parquet', columns=columns)


def load_training_sample(months, per_month, seed=0):
    """A random sample of ``per_month`` users from each of the given months, stacked."""
    parts = []
    for month in months:
        table = load_month(month)
        parts.append(table.sample(min(per_month, len(table)), random_state=seed))
    return pd.concat(parts, ignore_index=True)


def feature_matrix(table, drop=()):
    """Numeric feature matrix: booleans as 0/1, gender as a code, a negative category as missing.

    ``drop`` removes columns (for example ``PROFILE_COLUMNS``).
    """
    features = table[[c for c in month_columns(table.columns) if c not in drop]].copy()
    for column in features.columns:
        if column == 'gender':
            features[column] = features[column].map(GENDER_CODES).astype(float)
        else:
            features[column] = pd.to_numeric(features[column].astype(object).where(features[column].notna()),
                                             errors='coerce').astype(float)
    for column in ('city', 'registered_via', 'last_payment_method'):
        if column in features:
            features.loc[features[column] < 0, column] = np.nan
    return features


def rule_scores(table):
    """Scores of the one-feature baseline rules (higher means more likely to churn)."""
    return {
        'rule: no auto-renew': (table['last_auto_renew'] == 0).fillna(False).astype(float).to_numpy(),
        'rule: few listening days (30 days)': -table['active_days_30'].fillna(0).astype(float).to_numpy(),
        'rule: few transactions': -table['n_transactions'].fillna(0).astype(float).to_numpy()}


def make_logistic():
    def log_transform(frame):
        frame = frame.copy()
        for column in frame.columns:
            if column.startswith(_LOG_PREFIXES) or column in _LOG_NAMES:
                frame[column] = np.log1p(frame[column].clip(lower=0))
        return frame
    return log_transform


class LogisticModel:
    """Logistic regression on log-transformed, imputed (with missing indicators) and standardized features."""

    def __init__(self, columns):
        self.columns = columns
        numeric = [c for c in columns if c not in CATEGORICAL]
        categorical = [c for c in CATEGORICAL if c in columns]
        self.log_transform = make_logistic()
        self.pipeline = Pipeline([
            ('prepare', ColumnTransformer([
                ('numeric', Pipeline([('impute', SimpleImputer(strategy='median', add_indicator=True)),
                                      ('scale', StandardScaler())]), numeric),
                ('categorical', Pipeline([('impute', SimpleImputer(strategy='most_frequent')),
                                          ('onehot', OneHotEncoder(handle_unknown='ignore', min_frequency=200))]),
                 categorical)])),
            ('model', LogisticRegression(C=1.0, max_iter=300))])

    def fit(self, features, y):
        self.pipeline.fit(self.log_transform(features), y)
        return self

    def predict_proba(self, features):
        return self.pipeline.predict_proba(self.log_transform(features))[:, 1]


def make_boosting(columns, seed=0):
    """Gradient boosting with fixed settings (no tuning); the category codes are treated as categories."""
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, max_leaf_nodes=31,
                                          min_samples_leaf=200, l2_regularization=1.0, early_stopping=False,
                                          categorical_features=[c for c in CATEGORICAL if c in columns],
                                          random_state=seed)
