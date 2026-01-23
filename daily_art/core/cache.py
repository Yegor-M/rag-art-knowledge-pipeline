from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


def sha1_text(s: str) -> str:
    return hashlib.sha1((s or "").encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FileCache:
    root: Path

    def _path_for_key(self, namespace: str, key: str, suffix: str = ".json") -> Path:
        h = sha1_text(key)
        return self.root / namespace / f"{h}{suffix}"

    def get_json(self, namespace: str, key: str) -> Optional[Any]:
        p = self._path_for_key(namespace, key)
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def set_json(self, namespace: str, key: str, value: Any) -> Path:
        p = self._path_for_key(namespace, key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        return p

    def has(self, namespace: str, key: str) -> bool:
        return self._path_for_key(namespace, key).exists()