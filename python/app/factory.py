"""Builds the MemberProvider from configuration.

demo  -> synthetic members + in-memory overlay (runs with no Salesforce, no DB)
salesforce -> Salesforce source + Azure Table overlay (production)
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
    if config.provider == "demo":
        source: MemberSource = SyntheticMemberSource(group_code=config.demo_group_code)
        overlay: OverlayStore = InMemoryOverlayStore()
    else:
        source = SalesforceMemberSource()
        overlay = _production_overlay()
    return HybridMemberProvider(source, overlay)


def _production_overlay() -> OverlayStore:
    if config.overlay_connection_string:
        from .overlay.azure_table import AzureTableOverlayStore

        return AzureTableOverlayStore(config.overlay_connection_string, config.overlay_table_name)
    return InMemoryOverlayStore()
