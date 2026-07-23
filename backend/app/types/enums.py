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
    FIR_SEARCH = "FIR_SEARCH"
    FIR_EXPORT_PDF = "FIR_EXPORT_PDF"
    CCTNS_SYNC = "CCTNS_SYNC"

    # Documents
    DOCUMENT_GENERATE = "DOCUMENT_GENERATE"
    DOCUMENT_EXPORT_PDF = "DOCUMENT_EXPORT_PDF"

    # Case Diary
    DIARY_ENTRY_ADD = "DIARY_ENTRY_ADD"
    DIARY_ENTRY_DELETE = "DIARY_ENTRY_DELETE"

    # Evidence
    EVIDENCE_UPLOAD = "EVIDENCE_UPLOAD"
    EVIDENCE_ACCESS = "EVIDENCE_ACCESS"
    EVIDENCE_VERIFY = "EVIDENCE_VERIFY"

    # Case Linkage
    CASE_LINK = "CASE_LINK"

    # Legal
    LEGAL_QUERY = "LEGAL_QUERY"

    # Translation
    TRANSLATE = "TRANSLATE"


class ResourceType(str, Enum):
    """Resource types for audit log entries."""

    OFFICER = "officer"
    FIR = "fir"
    EVIDENCE = "evidence"
    CASE_LINK = "case_link"
    LEGAL_QUERY = "legal_query"
    DOCUMENT = "document"
    CASE_DIARY = "case_diary"


class SupportedLanguage(str, Enum):
    """Supported languages for translation and STT."""

    ENGLISH = "en"
    HINDI = "hi"
    GUJARATI = "gu"


class DocumentType(str, Enum):
    """Types of legal documents that can be auto-generated."""

    CHARGESHEET = "chargesheet"
    MEDICAL_LETTER = "medical_letter"
    REMAND_REQUEST = "remand_request"
    SEIZURE_RECEIPT = "seizure_receipt"
    COURT_CUSTODY_LETTER = "court_custody_letter"
    ACCUSED_PANCHANAMA = "accused_panchanama"
    FACE_ID_FORM = "face_id_form"


class CaseDiaryEntryType(str, Enum):
    """Types of entries in the case diary timeline."""

    COMPLAINT_RECEIVED = "complaint_received"
    FIR_REGISTERED = "fir_registered"
    INVESTIGATION_STARTED = "investigation_started"
    WITNESS_EXAMINED = "witness_examined"
    EVIDENCE_SEIZED = "evidence_seized"
    SPOT_VISIT = "spot_visit"
    ARREST_MADE = "arrest_made"
    REMAND_REQUESTED = "remand_requested"
    CHARGESHEET_FILED = "chargesheet_filed"
    COURT_HEARING = "court_hearing"
    OTHER = "other"
