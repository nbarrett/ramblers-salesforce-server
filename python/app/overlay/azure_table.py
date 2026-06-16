"""Azure Table Storage overlay store.

Cheap key/value persistence keyed by salesforceId, living in the same storage
account the Function App already needs. azure-data-tables is imported lazily so
the app runs without it (demo / local). For GDPR, deploy the storage account in a
UK region and rely on storage-service encryption at rest; `delete` supports
erasure of a member's overlay attributes.
"""

from __future__ import annotations

import json


class AzureTableOverlayStore:
    def __init__(self, connection_string: str, table_name: str = "memberoverlay") -> None:
        from azure.data.tables import TableServiceClient

        service = TableServiceClient.from_connection_string(connection_string)
        self._table = service.create_table_if_not_exists(table_name)
        self._partition = "member"

    def read(self, salesforce_id: str) -> dict[str, object]:
        from azure.core.exceptions import ResourceNotFoundError

        try:
            entity = self._table.get_entity(self._partition, salesforce_id)
        except ResourceNotFoundError:
            return {}
        raw = entity.get("attributes", "{}")
        parsed: dict[str, object] = json.loads(raw)
        return parsed

    def read_many(self, salesforce_ids: list[str]) -> dict[str, dict[str, object]]:
        result: dict[str, dict[str, object]] = {}
        for sid in salesforce_ids:
            attrs = self.read(sid)
            if attrs:
                result[sid] = attrs
        return result

    def write(self, salesforce_id: str, attributes: dict[str, object]) -> None:
        current = self.read(salesforce_id)
        current.update(attributes)
        self._table.upsert_entity(
            {
                "PartitionKey": self._partition,
                "RowKey": salesforce_id,
                "attributes": json.dumps(current),
            }
        )

    def delete(self, salesforce_id: str) -> None:
        from azure.core.exceptions import ResourceNotFoundError

        try:
            self._table.delete_entity(self._partition, salesforce_id)
        except ResourceNotFoundError:
            pass
