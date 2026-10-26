"""Prefetch January 2026 Elexon data into data/cache."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.elexon import fetch_january_2026_bundle  # noqa: E402


def main() -> None:
    bundle = fetch_january_2026_bundle(use_cache=False)
    print(
        f"Cached {len(bundle['actuals'])} actuals and "
        f"{len(bundle['forecasts'])} forecast rows "
        f"(fetched_at={bundle['fetched_at']})"
    )


if __name__ == "__main__":
    main()
