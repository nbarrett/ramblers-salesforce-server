"""Builds the MemberProvider from configuration.

The data source and the overlay store are chosen independently:
  source  -> synthetic (PROVIDER=demo) or Salesforce (PROVIDER=salesforce)
  overlay -> Azure Table when OVERLAY_CONNECTION_STRING is set, else in-memory

So the overlay can persist to a real Azure Table even with the demo source - the
extension fields it owns live outside Salesforce regardless of the source.
"""

from __future__ import annotations

from .config import config
from .member_provider import MemberProvider
from .overlay.memory import InMemoryOverlayStore
from .overlay.store import OverlayStore
from .providers.hybrid_member_provider import HybridMemberProvider
from .sources.base import MemberSource
from .sources.salesforce import SalesforceMemberSource
from .sources.synthetic import SyntheticMemberSource


def build_provider() -> MemberProvider:
    source: MemberSource
    if config.provider == "demo":
        source = SyntheticMemberSource(group_code=config.demo_group_code)
    else:
        source = SalesforceMemberSource()
    return HybridMemberProvider(source, build_overlay())


def build_overlay() -> OverlayStore:
    if config.overlay_connection_string:
        from .overlay.azure_table import AzureTableOverlayStore

        return AzureTableOverlayStore(config.overlay_connection_string, config.overlay_table_name)
    return InMemoryOverlayStore()
