"""Vercel serverless entry — wraps FastAPI with Mangum."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

# Prefer baked cache shipped in the repo
os.environ.setdefault("CACHE_DIR", str(ROOT / "data" / "cache"))

from mangum import Mangum  # noqa: E402
from app.main import app  # noqa: E402

handler = Mangum(app, lifespan="off")
