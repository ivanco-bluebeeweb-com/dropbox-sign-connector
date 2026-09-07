"""Connection management for Dropbox Sign Connector."""
from __future__ import annotations
import uuid, json
from typing import Any
from imperal_sdk import ActionResult
from app import chat
from schemas import (
    NoParams, ConnectParams, ConnectionIdParams, ConnectionRecord, ConnectionList, DeleteResult
)
from dropbox_sign_client import DropboxSignClient

_SECRET = "dropbox_sign_connections"

def _mask(v: str) -> str:
    return v[:4] + "…" + v[-4:] if len(v) > 8 else "***"

async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET)
    if not raw: return []
    try: data = json.loads(raw)
    except: return []
    return data if isinstance(data, list) else []

async def _save_connections(ctx, conns: list[dict]) -> None:
    await ctx.secrets.set(_SECRET, json.dumps(conns))

async def resolve_client(ctx, connection_id: str = "") -> DropboxSignClient:
    conns = await _load_connections(ctx)
    if not conns:
        raise ValueError("No Dropbox Sign connections configured. Use connect_dropbox_sign first.")
    conn = None
    if connection_id:
        for c in conns:
            if c.get("id") == connection_id:
                conn = c
                break
        if not conn:
            raise ValueError(f"Connection {connection_id} not found.")
    else:
        for c in conns:
            if c.get("is_active"):
                conn = c
                break
        if not conn:
            conn = conns[0]
    return DropboxSignClient(api_key=conn["api_key"], base_url=conn.get("base_url", ""))

@chat.function(
    "connect_dropbox_sign",
    "Connect Dropbox Sign account via credentials.",
    action_type="write",
    chain_callable=True,
    event="dropbox-sign-connector.connect_dropbox_sign",
    effects=["create:connection"],
    data_model=ConnectionRecord
)
async def connect_dropbox_sign(ctx, params: ConnectParams) -> ActionResult[ConnectionRecord]:
    client = DropboxSignClient(api_key=params.api_key, base_url=params.base_url)
    res = await client.verify_auth()
    if res.get("status") == "error":
        return ActionResult.error(f"Failed to authenticate with Dropbox Sign: {res.get('error')}")

    conns = await _load_connections(ctx)
    cid = f"conn_{uuid.uuid4().hex[:8]}"
    record = {
        "id": cid,
        "label": params.label or "Primary Dropbox Sign",
        "api_key": params.api_key,
        "masked_key": _mask(params.api_key),
        "base_url": params.base_url,
        "is_active": True
    }
    for c in conns:
        c["is_active"] = False
    conns.append(record)
    await _save_connections(ctx, conns)
    return ActionResult.success(ConnectionRecord(**record), summary=f"Connected to Dropbox Sign ({record['label']}).")

@chat.function(
    "list_connections",
    "List configured Dropbox Sign connections.",
    action_type="read",
    chain_callable=True,
    event="dropbox-sign-connector.list_connections",
    effects=["read:connections"],
    data_model=ConnectionList
)
async def list_connections(ctx, params: NoParams) -> ActionResult[ConnectionList]:
    conns = await _load_connections(ctx)
    recs = [ConnectionRecord(**c) for c in conns]
    return ActionResult.success(ConnectionList(connections=recs, total=len(recs)), summary=f"Found {len(recs)} Dropbox Sign connection(s).")

@chat.function(
    "disconnect_dropbox_sign",
    "Disconnect Dropbox Sign account and delete stored credentials.",
    action_type="destructive",
    chain_callable=True,
    event="dropbox-sign-connector.disconnect_dropbox_sign",
    effects=["delete:connection"],
    data_model=DeleteResult
)
async def disconnect_dropbox_sign(ctx, params: ConnectionIdParams) -> ActionResult[DeleteResult]:
    conns = await _load_connections(ctx)
    if not conns:
        return ActionResult.success(DeleteResult(success=True, message="No active connections to disconnect."), summary="Nothing to disconnect.")
    if params.connection_id:
        conns = [c for c in conns if c.get("id") != params.connection_id]
    else:
        conns = []
    await _save_connections(ctx, conns)
    return ActionResult.success(DeleteResult(success=True, message="Disconnected Dropbox Sign."), summary="Disconnected connection.")
