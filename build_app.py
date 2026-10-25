"""Reconstruct app.py from base64 part files. Run once: python build_app.py"""
import base64
from pathlib import Path

root = Path(__file__).resolve().parent
parts_dir = root / "app_parts"
chunks = sorted(parts_dir.glob("*.b64"))
if not chunks:
    raise SystemExit("No app_parts/*.b64 files found")
data = "".join(p.read_text().strip() for p in chunks)
(root / "app.py").write_bytes(base64.b64decode(data))
print("Created app.py successfully. You can delete app_parts/ and build_app.py if you want.")
