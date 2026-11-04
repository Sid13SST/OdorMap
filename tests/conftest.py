import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from odormap.data import DATA_PATH  # noqa: E402

requires_data = pytest.mark.skipif(
    not DATA_PATH.exists(), reason="dataset not fetched (run scripts/fetch_data.py)"
)
