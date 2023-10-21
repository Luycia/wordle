from pathlib import Path
from typing import Any, List


def write_lines(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        for line in data:
            f.write(f'{line}\n')


def read_lines(path: str) -> List[Any]:
    with open(Path(path)) as f:
        return f.read().splitlines()
