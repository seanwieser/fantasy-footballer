"""
Orchestrate a headless screenshot of the League Highlights preview harness.

Starts a preview harness (scripts/preview/*.py) as a child, waits for it to serve, screenshots
it with headless Chrome, then tears it down via its /quit route. Self-contained: only ever
manages its own child process (never the live app or the DuckDB file).

Usage:  PYTHONPATH=src/fantasy_footballer poetry run python3 scripts/preview/run.py [harness.py] [out.png]
Output: /tmp/highlights_preview.png (default)
"""
import os
import subprocess
import sys
import time
import urllib.request

HARNESS = sys.argv[1] if len(sys.argv) > 1 else "scripts/preview/highlights.py"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/highlights_preview.png"
PORT = 8099
BASE = f"http://127.0.0.1:{PORT}"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

env = dict(os.environ, PYTHONPATH="src/fantasy_footballer")
proc = subprocess.Popen(  # pylint: disable=consider-using-with
    ["poetry", "run", "python3", HARNESS], env=env)
try:
    for _ in range(120):
        try:
            with urllib.request.urlopen(BASE + "/", timeout=1):
                break
        except Exception:  # pylint: disable=broad-exception-caught
            time.sleep(0.3)
    else:
        print("server never came up", file=sys.stderr)
        sys.exit(1)
    time.sleep(1.0)  # let the websocket render settle
    subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         f"--screenshot={OUT}", "--window-size=1300,1700",
         "--virtual-time-budget=9000", BASE + "/"],
        check=False,
    )
    print("wrote", OUT)
finally:
    try:
        with urllib.request.urlopen(BASE + "/quit", timeout=2):
            pass
    except Exception:  # pylint: disable=broad-exception-caught
        pass
    try:
        proc.wait(timeout=8)
    except Exception:  # pylint: disable=broad-exception-caught
        proc.terminate()
