import shutil
from pathlib import Path


def safe_delete_path(path: Path):
    if path.exists():
        if not path.samefile('/'):
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            elif path.is_file():
                path.unlink()
        else:
            raise OSError.filename('root path deletion attempt')
