import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
# experiments/ for now (abm.py, metrics.py); src/ once Arm 1+ lives there.
sys.path.insert(0, str(ROOT / "experiments"))
sys.path.insert(0, str(ROOT / "src"))
