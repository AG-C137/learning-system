import sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"

sys.path.insert(0, str(SRC))

from app.main import main # type: ignore

main()