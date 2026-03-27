from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from uuid import uuid4

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def tmp_path() -> Path:
    temp_root = ROOT_DIR / ".tmp-test-ui"
    temp_root.mkdir(exist_ok=True)
    path = temp_root / uuid4().hex
    path.mkdir(exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
