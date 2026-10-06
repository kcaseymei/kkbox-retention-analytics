"""Reusable data-audit checks. DuckDB computes; each function returns a small pandas object.

A *relation* is the name of a table or view in the DuckDB connection: register a CSV with
``register_csv``, a Parquet file with ``register_parquet``, or a DataFrame with ``con.register``.
All checks are read-only. Columns are expected to be text (as registered here); numeric and
date interpretation happens inside each check, so source values are never altered.
Dates use the compact ``YYYYMMDD`` form used by KKBox files.
"""
import pandas as pd

DATE_PATTERN = r'[0-9]{8}'


def _q(name):
    return '"' + str(name).replace('"', '""') + '"'


def _literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def _columns(con, relation):
    return [row[0] for row in con.sql(f'DESCRIBE {_q(relation)}').fetchall()]


def _text(column):
    return f'CAST({_q(column)} AS VARCHAR)'


def _blank(column):
    return f"({_q(column)} IS NULL OR trim({_text(column)}) = '')"


def _date(column):
    text = _text(column)
    return f"CASE WHEN regexp_full_match({text}, '{DATE_PATTERN}') THEN TRY_STRPTIME({text}, '%Y%m%d') END"


def _number(column):
    return f'TRY_CAST({_text(column)} AS DOUBLE)'


def register_csv(con, name, path):
    """Expose a CSV as a view with every column read as text."""
    con.execute(f'CREATE OR REPLACE VIEW {_q(name)} AS '
                f'SELECT * FROM read_csv({_literal(path)}, header=true, all_varchar=true)')


def register_parquet(con, name, path):
    con.execute(f'CREATE OR REPLACE VIEW {_q(name)} AS SELECT * FROM read_parquet({_literal(path)})')


def table_summary(con, relation, key=None):
    """Row count, column count, and optionally the number of distinct key values."""
    rel = _q(relation)
    items = {'rows': con.sql(f'SELECT count(*) FROM {rel}').fetchone()[0],
             'columns': len(_columns(con, relation))}
    if key:
        items[f'unique_{key}'] = con.sql(f'SELECT count(DISTINCT {_q(key)}) FROM {rel}').fetchone()[0]
    return pd.Series(items, name='value').to_frame()


def missingness(con, relation, columns=None):
    """Missing (NULL or blank) count and percentage per column, from one scan."""
    columns = columns or _columns(con, relation)
    selects = ', '.join(f'count(*) FILTER (WHERE {_blank(c)}) AS {_q(c)}' for c in columns)
    row = con.sql(f'SELECT count(*) AS __rows, {selects} FROM {_q(relation)}').df().iloc[0]
    total = int(row['__rows'])
    out = pd.DataFrame({'missing': [int(row[c]) for c in columns]}, index=columns)
    out['percentage'] = out['missing'] / total * 100 if total else 0.0
    return out


def key_uniqueness(con, relation, keys):
    """Key completeness and duplication. Rows with a missing key part are counted separately."""
    keys = [keys] if isinstance(keys, str) else list(keys)
    rel, key_list = _q(relation), ', '.join(_q(k) for k in keys)
    missing = ' OR '.join(f'{_q(k)} IS NULL' for k in keys)
    row = con.sql(f"""
        WITH g AS (SELECT {key_list}, count(*) AS n FROM {rel} WHERE NOT ({missing}) GROUP BY {key_list})
        SELECT (SELECT count(*) FROM {rel})                                  AS rows,
               (SELECT count(*) FROM {rel} WHERE {missing})                  AS missing_key_rows,
               count(*)                                                       AS unique_keys,
               count(*) FILTER (WHERE n > 1)                                  AS duplicated_keys,
               CAST(coalesce(sum(n - 1) FILTER (WHERE n > 1), 0) AS BIGINT)  AS excess_rows,
               CAST(coalesce(sum(n) FILTER (WHERE n > 1), 0) AS BIGINT)      AS rows_in_duplicated_keys,
               CAST(coalesce(max(n), 0) AS BIGINT)                            AS max_rows_per_key
        FROM g
    """).df().iloc[0]
    return row.astype('int64').to_frame('value')


def exact_duplicates(con, relation, columns=None):
    """Rows beyond the first among rows identical on ``columns`` (default: all columns)."""
    columns = columns or _columns(con, relation)
    rel, column_list = _q(relation), ', '.join(_q(c) for c in columns)
    rows = con.sql(f'SELECT count(*) FROM {rel}').fetchone()[0]
    distinct = con.sql(f'SELECT count(*) FROM (SELECT DISTINCT {column_list} FROM {rel})').fetchone()[0]
    return pd.Series({'rows': rows, 'distinct_rows': distinct, 'excess_rows': rows - distinct}, name='value').to_frame()


def value_counts_pct(con, relation, column, limit=None):
    """Value distribution including missing values, most frequent first."""
    col, tail = _q(column), (f'LIMIT {int(limit)}' if limit else '')
    return con.sql(f"""
        SELECT {col} AS value, count(*) AS count,
               round(100.0 * count(*) / sum(count(*)) OVER (), 4) AS percentage
        FROM {_q(relation)} GROUP BY {col} ORDER BY count DESC, value {tail}
    """).df()


def numeric_range(con, relation, columns):
    """Missing, non-numeric, negative, zero counts and min/max per column, from one scan."""
    stats = ('missing', 'non_numeric', 'negative', 'zero', 'min', 'max')
    parts = []
    for c in columns:
        n = _number(c)
        parts += [f'count(*) FILTER (WHERE {_blank(c)}) AS {_q(c + "|missing")}',
                  f'count(*) FILTER (WHERE NOT {_blank(c)} AND {n} IS NULL) AS {_q(c + "|non_numeric")}',
                  f'count(*) FILTER (WHERE {n} < 0) AS {_q(c + "|negative")}',
                  f'count(*) FILTER (WHERE {n} = 0) AS {_q(c + "|zero")}',
                  f'min({n}) AS {_q(c + "|min")}', f'max({n}) AS {_q(c + "|max")}']
    row = con.sql(f'SELECT {", ".join(parts)} FROM {_q(relation)}').df().iloc[0]
    return pd.DataFrame({s: [row[f'{c}|{s}'] for c in columns] for s in stats}, index=list(columns))


def date_validity(con, relation, columns):
    """Missing, invalid (not a real YYYYMMDD date), earliest and latest per date column."""
    parts = []
    for c in columns:
        d = _date(c)
        parts += [f'count(*) FILTER (WHERE {_blank(c)}) AS {_q(c + "|missing")}',
                  f'count(*) FILTER (WHERE NOT {_blank(c)} AND {d} IS NULL) AS {_q(c + "|invalid")}',
                  f'min({d}) AS {_q(c + "|earliest")}', f'max({d}) AS {_q(c + "|latest")}']
    row = con.sql(f'SELECT {", ".join(parts)} FROM {_q(relation)}').df().iloc[0]
    return pd.DataFrame({s: [row[f'{c}|{s}'] for c in columns] for s in ('missing', 'invalid', 'earliest', 'latest')},
                        index=list(columns))


def monthly_coverage(con, relation, date_column, key=None):
    """Rows (and distinct keys) per calendar month; months with no rows do not appear."""
    distinct = f', count(DISTINCT {_q(key)}) AS keys' if key else ''
    return con.sql(f"""
        SELECT strftime({_date(date_column)}, '%Y-%m') AS month, count(*) AS rows{distinct}
        FROM {_q(relation)} GROUP BY month ORDER BY month
    """).df()


def flag_counts(con, relation, flags):
    """Rows matching each named SQL predicate, e.g. {'expiry_before_txn': '... < ...'}."""
    selects = ', '.join(f'count(*) FILTER (WHERE ({predicate})) AS {_q(name)}' for name, predicate in flags.items())
    row = con.sql(f'SELECT count(*) AS __rows, {selects} FROM {_q(relation)}').df().iloc[0]
    total = int(row['__rows'])
    out = pd.DataFrame({'rows': [int(row[n]) for n in flags]}, index=list(flags))
    out['percentage_of_all_rows'] = out['rows'] / total * 100 if total else 0.0
    return out


def coverage(con, left, right, key, right_key=None):
    """Share of distinct non-missing ``left`` keys that also appear in ``right``."""
    lk, rk = _q(key), _q(right_key or key)
    row = con.sql(f"""
        WITH l AS (SELECT DISTINCT {lk} AS k FROM {_q(left)} WHERE {lk} IS NOT NULL),
             r AS (SELECT DISTINCT {rk} AS k FROM {_q(right)} WHERE {rk} IS NOT NULL)
        SELECT count(*) AS left_keys, count(r.k) AS matched, count(*) - count(r.k) AS unmatched,
               100.0 * count(r.k) / nullif(count(*), 0) AS matched_percentage
        FROM l LEFT JOIN r ON l.k = r.k
    """).df().iloc[0]
    return row.to_frame('value')
