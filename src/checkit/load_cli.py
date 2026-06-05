"""Load CLI.

Examples:
    python -m checkit.load_cli                       # gate -> load -> metrics
    python -m checkit.load_cli --dag-id manual_test
"""

import argparse
import logging
import sys
from pathlib import Path

from checkit.config import Settings
from checkit.load import load_parquet, quality_gate, record_metrics

logger = logging.getLogger("checkit.load")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser(prog="checkit.load_cli")
    parser.add_argument("--parquet", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--dag-id", default=None)
    parser.add_argument("--min-valid-rate", type=float, default=0.5)
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    settings = Settings()
    parquet = args.parquet or settings.processed_dir / "dataset.parquet"
    report = args.report or settings.processed_dir / "run_report.json"
    dsn = settings.database_url.get_secret_value()
    enc_key = settings.enc_key.get_secret_value()

    quality_gate(report, args.min_valid_rate)
    stats = load_parquet(parquet, dsn, enc_key)
    record_metrics(report, stats, dsn, dag_id=args.dag_id)
    print(f"loaded={stats['rows_loaded']} skipped={stats['rows_skipped']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
