"""Benchmark: DuckDB read_csv bulk-load vs plain executemany.

Parametrized over several row counts to show where the crossover happens
relative to _READ_CSV_THRESHOLD (currently 100).

Run with:
    pytest tests/test_benchmark_duckdb.py -m benchmark -s -v
"""
import datetime
import time

import pytest

pytest.importorskip("duckdb", reason="duckdb not installed")

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Double,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    select,
)

from xml2db.dialect.duckdb import DuckDBDialect, _READ_CSV_THRESHOLD


@pytest.mark.benchmark
@pytest.mark.parametrize("n_rows", [10, 50, _READ_CSV_THRESHOLD, 500, 5_000])
def test_duckdb_bulk_load_speed(n_rows):
    """Compare read_csv (bulk_load=True) vs executemany (bulk_load=False) at different batch sizes."""
    engine = create_engine("duckdb:///:memory:")
    meta = MetaData()

    def _make_table(name):
        return Table(
            name,
            meta,
            Column("id", Integer, key="id"),
            Column("label", String(100), key="label"),
            Column("score", Double, key="score"),
            Column("flag", Boolean, key="flag"),
            Column("ts", DateTime, key="ts"),
        )

    table_csv = _make_table(f"bench_csv_{n_rows}")
    table_em = _make_table(f"bench_em_{n_rows}")
    meta.create_all(engine)

    base = datetime.datetime(2024, 1, 1)
    records = [
        {
            "id": i,
            "label": f"row_{i}",
            "score": i * 0.1,
            "flag": i % 2 == 0,
            "ts": base + datetime.timedelta(seconds=i),
        }
        for i in range(n_rows)
    ]

    dialect = DuckDBDialect()

    t0 = time.perf_counter()
    with engine.begin() as conn:
        dialect.bulk_insert(conn, table_csv, records, bulk_load=True)
    t_csv = time.perf_counter() - t0

    t0 = time.perf_counter()
    with engine.begin() as conn:
        dialect.bulk_insert(conn, table_em, records, bulk_load=False)
    t_em = time.perf_counter() - t0

    speedup = t_em / t_csv if t_csv > 0 else float("inf")
    threshold_marker = " <-- threshold" if n_rows == _READ_CSV_THRESHOLD else ""
    print(
        f"\n[{n_rows:>5} rows{threshold_marker}]"
        f"  read_csv: {t_csv * 1000:6.1f} ms"
        f"  executemany: {t_em * 1000:6.1f} ms"
        f"  speedup: {speedup:.2f}x"
    )

    with engine.connect() as conn:
        n_csv = len(conn.execute(select(table_csv)).fetchall())
        n_em = len(conn.execute(select(table_em)).fetchall())

    assert n_csv == n_rows, f"read_csv path: expected {n_rows} rows, got {n_csv}"
    assert n_em == n_rows, f"executemany path: expected {n_rows} rows, got {n_em}"

    meta.drop_all(engine)
    engine.dispose()
