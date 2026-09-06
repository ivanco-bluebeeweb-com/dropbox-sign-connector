"""Extension declaration, capabilities, health check for Dropbox Sign Connector."""
from __future__ import annotations
import json
from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "dropbox-sign-connector",
    version="0.1.0",
    display_name="Dropbox Sign",
    icon="icon.svg",
    capabilities=["dropbox_sign:manage"],
    description="Official Imperal connector for Dropbox Sign (C30. Email Marketing & Newsletter). Manage operations securely."
)

chat = ChatExtension(ext)

@ext.health_check
async def health_check(ctx) -> dict:
    raw = await ctx.secrets.get("dropbox_sign_connections")
    try:
        count = len(json.loads(raw)) if raw else 0
    except Exception:
        count = 0
    return {
        "healthy": True,
        "detail": f"{count} Dropbox Sign connection(s) configured." if count else "Not connected yet."
    }
