"""Convert KKBox CSV files to Parquet without altering values; raw files remain unchanged.

Every column is stored as text (all_varchar) so no type guessing, date parsing, or cleaning
happens here. Row order is not guaranteed (preserve_insertion_order is off to bound memory).
Each conversion is verified by comparing CSV and Parquet row counts.
"""
import argparse
import json
from pathlib import Path
import time

import duckdb


def convert(csv_path, out_dir, con):
    parquet_path = out_dir / (csv_path.stem + '.parquet')
    if parquet_path.exists():
        raise FileExistsError(f'{parquet_path} exists; remove it or choose a new output directory.')
    started = time.perf_counter()
    source = f"read_csv('{csv_path}', header=true, all_varchar=true)"
    con.execute(f"COPY (SELECT * FROM {source}) TO '{parquet_path}' (FORMAT parquet, COMPRESSION zstd)")
    csv_rows = con.execute(f'SELECT count(*) FROM {source}').fetchone()[0]
    parquet_rows = con.execute(f"SELECT count(*) FROM read_parquet('{parquet_path}')").fetchone()[0]
    columns = [row[0] for row in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{parquet_path}')").fetchall()]
    return {'file': csv_path.name, 'csv_bytes': csv_path.stat().st_size, 'parquet_bytes': parquet_path.stat().st_size,
            'csv_rows': csv_rows, 'parquet_rows': parquet_rows, 'rows_match': csv_rows == parquet_rows,
            'columns': columns, 'elapsed_seconds': round(time.perf_counter() - started, 2)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_files', nargs='+', type=Path)
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--memory-limit', default='8GB')
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{args.memory_limit}'")
    con.execute(f"SET temp_directory='{args.out_dir / 'duckdb_tmp'}'")
    con.execute('SET preserve_insertion_order=false')
    results = []
    for path in args.csv_files:
        print(f'Converting {path.name}', flush=True)
        result = convert(path, args.out_dir, con)
        print(f"  rows: csv={result['csv_rows']:,} parquet={result['parquet_rows']:,} match={result['rows_match']}", flush=True)
        results.append(result)
    (args.out_dir / 'conversion_manifest.json').write_text(json.dumps(results, indent=2))
    if not all(r['rows_match'] for r in results):
        raise SystemExit('Row-count mismatch: do not use these Parquet files.')


if __name__ == '__main__':
    main()
