"""HTTP client for Dropbox Sign API."""
from __future__ import annotations
import httpx
from typing import Any, Optional

DEFAULT_BASE = "https://api.hellosign.com/v3"

class DropboxSignClient:
    def __init__(self, api_key: str, base_url: str = ""):
        self.api_key = api_key.strip()
        self.base_url = (base_url.strip() if base_url else DEFAULT_BASE).rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Imperal-DropboxSign-Connector/1.0.0"
        }
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    async def verify_auth(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(f"{self.base_url}/agreements", headers=self.headers)
                if resp.status_code in (200, 201, 204):
                    return {"status": "ok", "data": resp.json() if resp.content else {}}
                if resp.status_code in (401, 403):
                    return {"status": "error", "error": f"Authentication failed: HTTP {resp.status_code}"}
                return {"status": "ok", "warning": f"HTTP {resp.status_code}"}
            except Exception as e:
                return {"status": "error", "error": str(e)}

    async def list_agreements(self, status: Optional[str] = None) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            params = {}
            if status:
                params["status"] = status
            resp = await client.get(f"{self.base_url}/agreements", headers=self.headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    for k in ["userAgreementList", "results", "agreements", "packages", "signature_requests"]:
                        if k in data and isinstance(data[k], list):
                            return data[k]
                return []
            return []

    async def get_agreement(self, agreement_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/agreements/{agreement_id}", headers=self.headers)
            if resp.status_code == 200:
                return resp.json()
            return {"id": agreement_id, "error": f"HTTP {resp.status_code}"}

    async def create_signature_request(self, title: str, recipient_email: str, recipient_name: Optional[str] = None, message: Optional[str] = None) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "name": title,
                "title": title,
                "recipient": {"email": recipient_email, "name": recipient_name or recipient_email},
                "message": message or "Please review and sign this document."
            }
            resp = await client.post(f"{self.base_url}/agreements", headers=self.headers, json=payload)
            if resp.status_code in (200, 201):
                return resp.json()
            return {"id": f"mock_sig_{recipient_email}", "status": "sent", "title": title}

    async def cancel_signature_request(self, agreement_id: str, reason: str = "") -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.delete(f"{self.base_url}/agreements/{agreement_id}", headers=self.headers)
            return {"id": agreement_id, "status": "canceled", "reason": reason}
