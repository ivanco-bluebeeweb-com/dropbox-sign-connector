"""Pydantic schemas for Dropbox Sign Connector (C34. E-Signature & Agreement Management)."""
from __future__ import annotations
from typing import Any, Optional, List, Dict
from pydantic import BaseModel, Field

class NoParams(BaseModel):
    pass

class ConnectParams(BaseModel):
    label: str = Field(default="", description="Friendly connection label, e.g. Primary Dropbox Sign.")
    api_key: str = Field(description="Dropbox Sign API Key (Basic Auth).")
    base_url: str = Field(default="https://api.hellosign.com/v3", description="Dropbox Sign API base URL.")

class ConnectionIdParams(BaseModel):
    connection_id: str = Field(default="", description="Connection identifier (empty uses active connection).")

class ConnectionRecord(BaseModel):
    id: str
    label: str
    masked_key: str
    base_url: str
    is_active: bool

class ConnectionList(BaseModel):
    connections: list[ConnectionRecord]
    total: int

class DeleteResult(BaseModel):
    success: bool
    message: str

class AgreementRecord(BaseModel):
    id: str
    name: str
    status: str
    created_at: Optional[str] = None
    signers: List[str] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)

class AgreementList(BaseModel):
    agreements: list[AgreementRecord]
    total: int

class ListAgreementsParams(BaseModel):
    connection_id: str = Field(default="", description="Optional connection ID.")
    status: Optional[str] = Field(default=None, description="Optional status filter (e.g. OUT_FOR_SIGNATURE, SIGNED, COMPLETED).")

class GetAgreementParams(BaseModel):
    connection_id: str = Field(default="", description="Optional connection ID.")
    agreement_id: str = Field(description="Dropbox Sign agreement or signature request ID.")

class CreateSignatureRequestParams(BaseModel):
    connection_id: str = Field(default="", description="Optional connection ID.")
    title: str = Field(description="Document or agreement title.")
    recipient_email: str = Field(description="Signer email address.")
    recipient_name: Optional[str] = Field(default=None, description="Signer full name.")
    message: Optional[str] = Field(default=None, description="Message to signer.")

class CancelSignatureRequestParams(BaseModel):
    connection_id: str = Field(default="", description="Optional connection ID.")
    agreement_id: str = Field(description="Dropbox Sign agreement or signature request ID.")
    reason: Optional[str] = Field(default="Canceled by user request", description="Reason for cancellation.")

class ESignAuditReport(BaseModel):
    total_agreements: int
    pending_signatures: int
    completed_agreements: int
    expired_or_declined: int
    summary: str
