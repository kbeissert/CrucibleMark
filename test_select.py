import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.benchmark_utils import select_from_list

items = [("A", "Apple"), ("B", "Banana")]
# We just want to see how select_from_list takes args
help(select_from_list)
