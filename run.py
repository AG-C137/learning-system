import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))

from booklib.cli.main import main

main()