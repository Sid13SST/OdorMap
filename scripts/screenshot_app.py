"""Run the Streamlit app headless and capture README screenshots.

Requires requirements-dev.txt (playwright) and a Chromium build:
    pip install -r requirements-dev.txt
    python -m playwright install chromium
Set CHROMIUM_PATH to use an existing Chromium binary instead.

Writes app_vanillin.png (dropdown example, in the training set) and
app_new_molecule.png (typed SMILES of 5-propylvanillin, a vanillin analog that
is not in the Leffingwell set) to docs/screenshots/, or to --out.
"""
from __future__ import annotations

import argparse
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
# (file, dropdown example to pick or None, SMILES to type or None, expected membership text)
SHOTS = [
    ("app_vanillin.png", "Vanillin", None, "in training data (memorization possible)"),
    ("app_new_molecule.png", None, "CCCc1cc(C=O)cc(OC)c1O", "Not found in training data"),
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=OUT)
    out = ap.parse_args(argv).out
    out.mkdir(parents=True, exist_ok=True)
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
            page = browser.new_page(viewport={"width": 1280, "height": 1450},
                                    device_scale_factor=2)
            for fname, example, smiles, flag in SHOTS:
                page.goto(url)
                page.get_by_text("Top-10 odor descriptors").wait_for(timeout=60_000)
                if example:
                    page.locator("[data-testid='stSelectbox']").click()
                    page.locator("[role=option]").filter(
                        has_text=re.compile("^" + re.escape(example))).first.click()
                if smiles:
                    box = page.get_by_label("SMILES")
                    box.fill(smiles)
                    box.press("Enter")
                page.get_by_text(flag).wait_for(timeout=60_000)
                page.mouse.click(5, 5)  # drop focus so no input is highlighted
                page.get_by_text("Top-10 odor descriptors").wait_for()
                page.wait_for_timeout(1500)  # let images finish rendering
                path = out / fname
                page.screenshot(path=str(path), full_page=True)
                print(f"wrote {path} ({path.stat().st_size:,} bytes)")
            browser.close()
    finally:
        proc.terminate()
        proc.wait(timeout=10)
    return 0


if __name__ == "__main__":
    sys.exit(main())
