"""Resource handlers for Dropbox Sign Connector."""
from __future__ import annotations
from typing import Any
from imperal_sdk import ActionResult
from app import chat
from schemas import (
    NoParams, AgreementRecord, AgreementList, ListAgreementsParams,
    GetAgreementParams, CreateSignatureRequestParams, CancelSignatureRequestParams,
    DeleteResult, ESignAuditReport
)
from handlers_connection import resolve_client

@chat.function(
    "list_agreements",
    "List agreements or signature requests in Dropbox Sign.",
    action_type="read",
    chain_callable=True,
    event="dropbox-sign-connector.list_agreements",
    effects=["read:agreements"],
    data_model=AgreementList
)
async def list_agreements(ctx, params: ListAgreementsParams) -> ActionResult[AgreementList]:
    try:
        client = await resolve_client(ctx, params.connection_id)
        raw_agreements = await client.list_agreements(status=params.status)
        agreements = []
        for a in raw_agreements:
            aid = str(a.get("id") or a.get("agreementId") or a.get("signature_request_id") or "unknown")
            name = a.get("name") or a.get("title") or "Untitled Document"
            status = a.get("status") or "UNKNOWN"
            agreements.append(AgreementRecord(id=aid, name=name, status=status, raw=a))
        return ActionResult.success(AgreementList(agreements=agreements, total=len(agreements)), summary=f"Retrieved {len(agreements)} agreements from Dropbox Sign.")
    except Exception as e:
        return ActionResult.error(f"Error listing agreements: {e}")

@chat.function(
    "get_agreement",
    "Get details of one agreement or signature request in Dropbox Sign.",
    action_type="read",
    chain_callable=True,
    event="dropbox-sign-connector.get_agreement",
    effects=["read:agreement"],
    data_model=AgreementRecord
)
async def get_agreement(ctx, params: GetAgreementParams) -> ActionResult[AgreementRecord]:
    try:
        client = await resolve_client(ctx, params.connection_id)
        raw = await client.get_agreement(params.agreement_id)
        aid = str(raw.get("id") or raw.get("agreementId") or params.agreement_id)
        name = raw.get("name") or raw.get("title") or "Document"
        status = raw.get("status") or "ACTIVE"
        rec = AgreementRecord(id=aid, name=name, status=status, raw=raw)
        return ActionResult.success(rec, summary=f"Agreement {aid}: {status}.")
    except Exception as e:
        return ActionResult.error(f"Error getting agreement: {e}")

@chat.function(
    "create_signature_request",
    "Send a new document for signature via Dropbox Sign.",
    action_type="write",
    chain_callable=True,
    event="dropbox-sign-connector.create_signature_request",
    effects=["create:signature_request"],
    data_model=AgreementRecord
)
async def create_signature_request(ctx, params: CreateSignatureRequestParams) -> ActionResult[AgreementRecord]:
    try:
        client = await resolve_client(ctx, params.connection_id)
        res = await client.create_signature_request(
            title=params.title,
            recipient_email=params.recipient_email,
            recipient_name=params.recipient_name,
            message=params.message
        )
        aid = str(res.get("id") or res.get("agreementId") or f"sig_{params.recipient_email}")
        rec = AgreementRecord(id=aid, name=params.title, status="OUT_FOR_SIGNATURE", raw=res)
        return ActionResult.success(rec, summary=f"Created signature request '{params.title}' for {params.recipient_email}.")
    except Exception as e:
        return ActionResult.error(f"Error creating signature request: {e}")

@chat.function(
    "cancel_signature_request",
    "Cancel or void an in-flight signature request in Dropbox Sign.",
    action_type="destructive",
    chain_callable=True,
    event="dropbox-sign-connector.cancel_signature_request",
    effects=["delete:signature_request"],
    data_model=DeleteResult
)
async def cancel_signature_request(ctx, params: CancelSignatureRequestParams) -> ActionResult[DeleteResult]:
    try:
        client = await resolve_client(ctx, params.connection_id)
        res = await client.cancel_signature_request(params.agreement_id, reason=params.reason)
        return ActionResult.success(DeleteResult(success=True, message=f"Canceled signature request {params.agreement_id}."), summary=f"Canceled signature request {params.agreement_id}.")
    except Exception as e:
        return ActionResult.error(f"Error canceling signature request: {e}")

@chat.function(
    "audit_esign_health",
    "Audit in-flight signature requests, turnaround rates, and expired agreements in Dropbox Sign.",
    action_type="read",
    chain_callable=True,
    event="dropbox-sign-connector.audit_esign_health",
    effects=["read:audit"],
    data_model=ESignAuditReport
)
async def audit_esign_health(ctx, params: NoParams) -> ActionResult[ESignAuditReport]:
    try:
        client = await resolve_client(ctx)
        agreements = await client.list_agreements()
        pending = sum(1 for a in agreements if str(a.get("status", "")).upper() in ("OUT_FOR_SIGNATURE", "PENDING", "SENT"))
        completed = sum(1 for a in agreements if str(a.get("status", "")).upper() in ("SIGNED", "COMPLETED", "APPROVED"))
        expired = sum(1 for a in agreements if str(a.get("status", "")).upper() in ("EXPIRED", "DECLINED", "CANCELED"))
        rep = ESignAuditReport(
            total_agreements=len(agreements),
            pending_signatures=pending,
            completed_agreements=completed,
            expired_or_declined=expired,
            summary=f"Dropbox Sign health audit: {len(agreements)} total tracked agreements, {pending} pending signatures, {completed} completed."
        )
        return ActionResult.success(rep, summary=rep.summary)
    except Exception as e:
        return ActionResult.error(f"Error auditing e-sign health: {e}")
