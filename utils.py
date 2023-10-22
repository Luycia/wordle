import sys
from pathlib import Path
from typing import Any, List


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)
    return Path(base_path) / relative_path


def write_lines(path, data):
    path = resource_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        for line in data:
            f.write(f'{line}\n')


def read_lines(path: str) -> List[Any]:
    path = resource_path(path)
    with open(path) as f:
        return f.read().splitlines()
