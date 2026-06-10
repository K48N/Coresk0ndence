from __future__ import annotations

import argparse
from pathlib import Path

from bot.pipeline.daily import run_daily
from bot.settings import load_settings



def main() -> None:
    parser = argparse.ArgumentParser(description="Coresk0ndence newsletter generator")
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum stories to include in the newsletter.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Write newsletter files to this directory instead of output/.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the newsletter and print it without writing files.",
    )

    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    settings = load_settings(root, output_dir=args.output_dir)

    try:
        out = run_daily(settings, limit=max(1, args.limit), dry_run=args.dry_run)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    if args.dry_run:
        print(out["markdown"])
        return

    output_paths = out.get("output_paths", {})
    print(str(output_paths.get("markdown", settings.out_dir / "newsletter-latest.md")))
