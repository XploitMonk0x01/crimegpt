"""
Shared enumerations used across the application.

These enums are the single source of truth for:
    - Officer roles (RBAC)
    - FIR lifecycle status
    - Audit trail action types
"""

from enum import Enum


class OfficerRole(str, Enum):
    """Officer roles for RBAC enforcement."""

    CONSTABLE = "constable"
    INSPECTOR = "inspector"
    STATION_HEAD = "station_head"
    ADMIN = "admin"


class FIRStatus(str, Enum):
    """FIR lifecycle status transitions: draft → submitted → approved/rejected."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class AuditAction(str, Enum):
    """Immutable audit trail action types."""

    # Auth
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"

    # FIR
    FIR_CREATE = "FIR_CREATE"
    FIR_EDIT = "FIR_EDIT"
    FIR_SUBMIT = "FIR_SUBMIT"
    FIR_APPROVE = "FIR_APPROVE"
    FIR_REJECT = "FIR_REJECT"
    FIR_EXPORT_PDF = "FIR_EXPORT_PDF"

    # Evidence
    EVIDENCE_UPLOAD = "EVIDENCE_UPLOAD"
    EVIDENCE_ACCESS = "EVIDENCE_ACCESS"
    EVIDENCE_VERIFY = "EVIDENCE_VERIFY"

    # Case Linkage
    CASE_LINK = "CASE_LINK"

    # Legal
    LEGAL_QUERY = "LEGAL_QUERY"


class ResourceType(str, Enum):
    """Resource types for audit log entries."""

    OFFICER = "officer"
    FIR = "fir"
    EVIDENCE = "evidence"
    CASE_LINK = "case_link"
    LEGAL_QUERY = "legal_query"


class SupportedLanguage(str, Enum):
    """Supported languages for translation and STT."""

    ENGLISH = "en"
    HINDI = "hi"
    GUJARATI = "gu"
