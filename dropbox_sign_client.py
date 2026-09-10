"""HTTP client for Dropbox Sign (HelloSign) API."""
from __future__ import annotations
import httpx
import base64
from typing import Any, Optional

DEFAULT_BASE = "https://api.hellosign.com/v3"

class DropboxSignClient:
    def __init__(self, api_key: str, base_url: str = ""):
        self.api_key = api_key.strip()
        self.base_url = (base_url.strip() if base_url else DEFAULT_BASE).rstrip("/")
        
        if self.api_key.startswith("Bearer "):
            auth_header = self.api_key
        elif self.api_key.startswith("Basic "):
            auth_header = self.api_key
        else:
            # Dropbox Sign API Key is supplied via HTTP Basic Auth (key as username, blank password)
            raw = f"{self.api_key}:".encode("utf-8")
            auth_header = f"Basic {base64.b64encode(raw).decode('utf-8')}"
            
        self.headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "User-Agent": "Imperal-DropboxSign-Connector/1.0.0"
        }
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    async def verify_auth(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(f"{self.base_url}/account", headers=self.headers)
                if resp.status_code in (200, 201, 204):
                    return {"status": "ok", "data": resp.json() if resp.content else {}}
                return {"status": "error", "error": f"HTTP {resp.status_code}: {resp.text}"}
            except Exception as e:
                return {"status": "error", "error": str(e)}

    async def list_agreements(self, limit: int = 20) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/signature_request/list", headers=self.headers, params={"page_size": min(limit, 100)})
            if resp.status_code == 200:
                data = resp.json()
                if "signature_requests" in data:
                    return data["signature_requests"]
                if isinstance(data, list): return data
                return []
            return []

    async def get_agreement(self, agreement_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/signature_request/{agreement_id}", headers=self.headers)
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"HTTP {resp.status_code}: {resp.text}"}

    async def create_signature_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/signature_request/send", headers=self.headers, json=payload)
            if resp.status_code in (200, 201):
                return resp.json()
            return {"error": f"HTTP {resp.status_code}: {resp.text}"}

    async def cancel_signature_request(self, agreement_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/signature_request/cancel/{agreement_id}", headers=self.headers)
            if resp.status_code in (200, 204):
                return {"status": "cancelled", "signature_request_id": agreement_id}
            return {"error": f"HTTP {resp.status_code}: {resp.text}"}
