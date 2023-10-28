import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    relative_path = Path(relative_path)
    if relative_path.is_absolute():
        return relative_path
    base_path = getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent)
    return Path(base_path) / relative_path


def write_textlines(path: str, data: List[Any]) -> None:
    path = resource_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for line in data:
            f.write(f'{line}\n')


def read_textlines(path: str, nullable: bool = False) -> List[Any]:
    return read_file(path, nullable).splitlines()


def read_file(path: str, nullable: bool = False) -> str:
    path = resource_path(path)
    if nullable and not path.exists():
        return None
    
    with open(path, encoding='utf-8') as f:
        return f.read()


def read_json(path: str, nullable: bool = False) -> Dict[str, Any]:
    path = resource_path(path)
    if nullable and not path.exists():
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def write_jsons(path: str, obj: str) -> None:
    write_json(path, json.loads(obj))


def write_json(path: str, obj: Any) -> None:
    path = resource_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=4)
