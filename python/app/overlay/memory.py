from __future__ import annotations

from typing import Optional


class InMemoryOverlayStore:
    def __init__(self, seed: Optional[dict[str, dict[str, object]]] = None) -> None:
        self._data: dict[str, dict[str, object]] = {k: dict(v) for k, v in (seed or {}).items()}

    def read(self, salesforce_id: str) -> dict[str, object]:
        return dict(self._data.get(salesforce_id, {}))

    def read_many(self, salesforce_ids: list[str]) -> dict[str, dict[str, object]]:
        return {sid: dict(self._data[sid]) for sid in salesforce_ids if sid in self._data}

    def write(self, salesforce_id: str, attributes: dict[str, object]) -> None:
        self._data.setdefault(salesforce_id, {}).update(attributes)

    def delete(self, salesforce_id: str) -> None:
        self._data.pop(salesforce_id, None)
