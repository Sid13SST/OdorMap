"""Run the Streamlit app headless and capture README screenshots.

Requires requirements-dev.txt (playwright) and a Chromium build:
    pip install -r requirements-dev.txt
    python -m playwright install chromium
Set CHROMIUM_PATH to use an existing Chromium binary instead.

Writes docs/screenshots/app_vanillin.png and docs/screenshots/app_new_molecule.png.
"""
from __future__ import annotations

import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
# (file, example to pick from the dropdown, expected membership text)
SHOTS = [
    ("app_vanillin.png", "Vanillin", "in training data (memorization possible)"),
    ("app_new_molecule.png", "5-Propylvanillin", "new molecule (true generalization)"),
]


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_http(url: str, timeout: float = 60) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            urlopen(url, timeout=2)
            return
        except OSError:
            time.sleep(0.5)
    raise TimeoutError(url)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    port = free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py"),
         "--server.headless", "true", "--server.port", str(port),
         "--browser.gatherUsageStats", "false", "--theme.base", "light"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    try:
        wait_http(url + "/_stcore/health")
        with sync_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM_PATH"]} \
                if os.environ.get("CHROMIUM_PATH") else {}
            browser = p.chromium.launch(**kw)
            page = browser.new_page(viewport={"width": 1280, "height": 1250},
                                    device_scale_factor=2)
            for fname, example, flag in SHOTS:
                page.goto(url)
                page.get_by_text("Top-10 odor descriptors").wait_for(timeout=60_000)
                page.locator("[data-testid='stSelectbox']").click()
                page.locator("[role=option]").filter(
                    has_text=re.compile("^" + re.escape(example))).first.click()
                page.get_by_text(flag).wait_for(timeout=60_000)
                page.mouse.click(5, 5)  # drop focus so no input is highlighted
                page.get_by_text("Top-10 odor descriptors").wait_for()
                page.wait_for_timeout(1500)  # let images finish rendering
                path = OUT / fname
                page.screenshot(path=str(path), full_page=True)
                print(f"wrote {path} ({path.stat().st_size:,} bytes)")
            browser.close()
    finally:
        proc.terminate()
        proc.wait(timeout=10)
    return 0


if __name__ == "__main__":
    sys.exit(main())
