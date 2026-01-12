"""Document and pattern data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import json


class DocumentType(str, Enum):
    """Supported document types for classification."""

    RECEIPT = "receipt"
    BILL = "bill"
    TAX_DOCUMENT = "tax_document"
    BANK_STATEMENT = "bank_statement"
    INVOICE = "invoice"
    CONTRACT = "contract"
    MEDICAL = "medical"
    INSURANCE = "insurance"
    INVESTMENT = "investment"
    PAYSLIP = "payslip"
    IDENTITY = "identity"
    CORRESPONDENCE = "correspondence"
    MANUAL = "manual"
    PHOTO = "photo"
    GENERAL = "general"

    @classmethod
    def from_string(cls, value: str) -> "DocumentType":
        """Convert string to DocumentType, defaulting to GENERAL."""
        try:
            return cls(value.lower().replace(" ", "_"))
        except ValueError:
            return cls.GENERAL


@dataclass
class DocumentInfo:
    """Information extracted from a document."""

    file_path: str
    original_name: str
    document_type: DocumentType

    # Extracted fields (populated by AI analysis)
    date: Optional[str] = None
    year: Optional[str] = None
    month: Optional[str] = None
    merchant: Optional[str] = None
    amount: Optional[str] = None
    account_number: Optional[str] = None
    form_type: Optional[str] = None
    institution: Optional[str] = None
    description: Optional[str] = None

    # Additional metadata
    mime_type: Optional[str] = None
    file_size: Optional[int] = None

    # AI confidence
    confidence: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "original_name": self.original_name,
            "document_type": self.document_type.value,
            "date": self.date,
            "year": self.year,
            "month": self.month,
            "merchant": self.merchant,
            "amount": self.amount,
            "account_number": self.account_number,
            "form_type": self.form_type,
            "institution": self.institution,
            "description": self.description,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentInfo":
        """Create from dictionary."""
        data = data.copy()
        data["document_type"] = DocumentType.from_string(data.get("document_type", "general"))
        return cls(**data)

    def get_token_values(self) -> dict[str, str]:
        """Get available token values for pattern substitution."""
        values = {}

        if self.date:
            values["Date"] = self.date
            values["Date:YYYY-MM-DD"] = self.date
            # Try to parse and format
            try:
                dt = datetime.strptime(self.date, "%Y-%m-%d")
                values["Date:YYYY"] = dt.strftime("%Y")
                values["Date:YYYY-MM"] = dt.strftime("%Y-%m")
                values["Date:MM-DD"] = dt.strftime("%m-%d")
            except ValueError:
                pass

        if self.year:
            values["Year"] = self.year
            values["Date:YYYY"] = self.year

        if self.month:
            values["Month"] = self.month

        if self.merchant:
            values["Merchant"] = self.merchant
            values["Vendor"] = self.merchant

        if self.amount:
            values["Amount"] = self.amount

        if self.account_number:
            values["Account Number"] = self.account_number
            values["Last 4 Digits"] = self.account_number[-4:] if len(self.account_number) >= 4 else self.account_number

        if self.form_type:
            values["Form Type"] = self.form_type
            values["Form"] = self.form_type

        if self.institution:
            values["Institution"] = self.institution
            values["Bank Name"] = self.institution
            values["Service Provider"] = self.institution

        if self.description:
            values["Description"] = self.description
            values["Title"] = self.description
            values["Subject"] = self.description
            values["Items"] = self.description

        return values


@dataclass
class PatternRule:
    """A naming pattern rule that can be learned and applied."""

    id: str
    document_type: DocumentType
    pattern: str  # e.g., "{Date:YYYY} - {Form Type} - {Institution}"

    # Pattern metadata
    name: str = ""
    description: str = ""

    # Learning data
    use_count: int = 0
    last_used: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Matching criteria (for auto-selection)
    match_keywords: list[str] = field(default_factory=list)
    match_institutions: list[str] = field(default_factory=list)
    priority: int = 0  # Higher priority rules are tried first

    # Is this a user-created or default pattern?
    is_custom: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "document_type": self.document_type.value,
            "pattern": self.pattern,
            "name": self.name,
            "description": self.description,
            "use_count": self.use_count,
            "last_used": self.last_used,
            "created_at": self.created_at,
            "match_keywords": self.match_keywords,
            "match_institutions": self.match_institutions,
            "priority": self.priority,
            "is_custom": self.is_custom,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PatternRule":
        """Create from dictionary."""
        data = data.copy()
        data["document_type"] = DocumentType.from_string(data.get("document_type", "general"))
        return cls(**data)

    def matches_document(self, doc: DocumentInfo) -> bool:
        """Check if this pattern should apply to a document."""
        if self.document_type != doc.document_type:
            return False

        # Check keyword matches
        doc_text = " ".join(filter(None, [
            doc.description,
            doc.institution,
            doc.merchant,
            doc.form_type,
        ])).lower()

        for keyword in self.match_keywords:
            if keyword.lower() in doc_text:
                return True

        for institution in self.match_institutions:
            if doc.institution and institution.lower() in doc.institution.lower():
                return True

        # If no specific matches required, it's a general pattern for this type
        if not self.match_keywords and not self.match_institutions:
            return True

        return False

    def apply_to_document(self, doc: DocumentInfo) -> str:
        """Apply this pattern to a document, returning the new filename."""
        result = self.pattern
        token_values = doc.get_token_values()

        # Replace all tokens
        for token, value in token_values.items():
            result = result.replace(f"{{{token}}}", value)

        # Remove any unreplaced tokens
        import re
        result = re.sub(r'\{[^}]+\}', '', result)

        # Clean up multiple spaces and dashes
        result = re.sub(r'\s+', ' ', result)
        result = re.sub(r'\s*-\s*-\s*', ' - ', result)
        result = re.sub(r'^\s*-\s*', '', result)
        result = re.sub(r'\s*-\s*$', '', result)
        result = result.strip()

        return result


@dataclass
class RenameResult:
    """Result of a rename operation."""

    original_path: str
    original_name: str
    new_name: str
    new_path: str
    document_type: DocumentType
    pattern_used: str
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "original_path": self.original_path,
            "original_name": self.original_name,
            "new_name": self.new_name,
            "new_path": self.new_path,
            "document_type": self.document_type.value,
            "pattern_used": self.pattern_used,
            "success": self.success,
            "error": self.error,
        }
