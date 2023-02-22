from pathlib import Path
import os

ROOT_DIR = Path(os.curdir).absolute().parent
DATABASE_DIR = os.path.join(ROOT_DIR, 'database')