"""Default naming patterns for different document types."""

from ..models.document import DocumentType

# Document type descriptions for AI classification
DOCUMENT_TYPES = {
    DocumentType.RECEIPT: {
        "name": "Receipt",
        "description": "Purchase receipts from stores, restaurants, online orders",
        "keywords": ["receipt", "purchase", "order", "transaction", "payment"],
        "extract_fields": ["date", "merchant", "amount", "description"],
    },
    DocumentType.BILL: {
        "name": "Bill",
        "description": "Utility bills, service provider statements, subscription charges",
        "keywords": ["bill", "statement", "due", "utility", "service"],
        "extract_fields": ["date", "institution", "amount", "account_number"],
    },
    DocumentType.TAX_DOCUMENT: {
        "name": "Tax Document",
        "description": "Tax forms like W-2, 1099, K-1, tax returns, tax statements",
        "keywords": ["tax", "w-2", "w2", "1099", "k-1", "k1", "irs", "return", "1040"],
        "extract_fields": ["year", "form_type", "institution"],
    },
    DocumentType.BANK_STATEMENT: {
        "name": "Bank Statement",
        "description": "Bank account statements, transaction histories",
        "keywords": ["bank", "statement", "account", "balance", "transaction"],
        "extract_fields": ["date", "institution", "account_number"],
    },
    DocumentType.INVOICE: {
        "name": "Invoice",
        "description": "Business invoices, billing statements",
        "keywords": ["invoice", "inv", "billing", "due"],
        "extract_fields": ["date", "merchant", "amount", "description"],
    },
    DocumentType.CONTRACT: {
        "name": "Contract",
        "description": "Legal contracts, agreements, terms of service",
        "keywords": ["contract", "agreement", "terms", "signed"],
        "extract_fields": ["date", "institution", "description"],
    },
    DocumentType.MEDICAL: {
        "name": "Medical Document",
        "description": "Medical records, lab results, prescriptions, EOBs",
        "keywords": ["medical", "health", "doctor", "hospital", "lab", "prescription", "eob"],
        "extract_fields": ["date", "institution", "description"],
    },
    DocumentType.INSURANCE: {
        "name": "Insurance Document",
        "description": "Insurance policies, claims, ID cards",
        "keywords": ["insurance", "policy", "claim", "coverage", "premium"],
        "extract_fields": ["date", "institution", "account_number", "description"],
    },
    DocumentType.INVESTMENT: {
        "name": "Investment Document",
        "description": "Brokerage statements, 401k, IRA, stock transactions",
        "keywords": ["investment", "brokerage", "401k", "ira", "stock", "dividend", "capital gain"],
        "extract_fields": ["date", "institution", "account_number"],
    },
    DocumentType.PAYSLIP: {
        "name": "Pay Slip",
        "description": "Paycheck stubs, salary statements",
        "keywords": ["pay", "salary", "wage", "paycheck", "stub", "earnings"],
        "extract_fields": ["date", "institution", "amount"],
    },
    DocumentType.IDENTITY: {
        "name": "Identity Document",
        "description": "ID cards, passports, licenses, certifications",
        "keywords": ["passport", "license", "id", "identification", "certificate"],
        "extract_fields": ["date", "description"],
    },
    DocumentType.CORRESPONDENCE: {
        "name": "Correspondence",
        "description": "Letters, notices, official communications",
        "keywords": ["letter", "notice", "dear", "sincerely", "correspondence"],
        "extract_fields": ["date", "institution", "description"],
    },
    DocumentType.MANUAL: {
        "name": "Manual/Guide",
        "description": "Product manuals, user guides, instructions",
        "keywords": ["manual", "guide", "instructions", "user", "setup"],
        "extract_fields": ["description", "institution"],
    },
    DocumentType.PHOTO: {
        "name": "Photo",
        "description": "Photographs, images, screenshots",
        "keywords": ["photo", "image", "picture", "screenshot"],
        "extract_fields": ["date", "description"],
    },
    DocumentType.GENERAL: {
        "name": "General Document",
        "description": "Documents that don't fit other categories",
        "keywords": [],
        "extract_fields": ["date", "description"],
    },
}

# Default naming patterns for each document type
DEFAULT_PATTERNS = {
    DocumentType.RECEIPT: [
        {
            "id": "receipt_default",
            "pattern": "{Date:YYYY-MM-DD} - {Merchant} - {Amount}",
            "name": "Standard Receipt",
            "description": "Date, merchant name, and amount",
            "priority": 0,
        },
        {
            "id": "receipt_detailed",
            "pattern": "{Date:YYYY-MM-DD} - {Merchant} - {Items} - {Amount}",
            "name": "Detailed Receipt",
            "description": "Includes item description",
            "priority": -1,
        },
    ],
    DocumentType.BILL: [
        {
            "id": "bill_default",
            "pattern": "{Date:YYYY-MM} - {Service Provider} - {Amount}",
            "name": "Standard Bill",
            "description": "Month, provider, and amount",
            "priority": 0,
        },
        {
            "id": "bill_with_account",
            "pattern": "{Date:YYYY-MM} - {Service Provider} - {Account Number}",
            "name": "Bill with Account",
            "description": "Includes account number",
            "priority": -1,
        },
    ],
    DocumentType.TAX_DOCUMENT: [
        {
            "id": "tax_k1",
            "pattern": "{Year} - K-1 - {Institution}",
            "name": "K-1 Form",
            "description": "K-1 partnership/S-corp tax forms",
            "match_keywords": ["k-1", "k1", "schedule k"],
            "priority": 10,
        },
        {
            "id": "tax_1099",
            "pattern": "{Year} - 1099 - {Institution}",
            "name": "1099 Form",
            "description": "1099 tax forms",
            "match_keywords": ["1099"],
            "priority": 10,
        },
        {
            "id": "tax_w2",
            "pattern": "{Year} - W-2 - {Institution}",
            "name": "W-2 Form",
            "description": "W-2 wage statements",
            "match_keywords": ["w-2", "w2"],
            "priority": 10,
        },
        {
            "id": "tax_default",
            "pattern": "{Year} - {Form Type} - {Institution}",
            "name": "Standard Tax Document",
            "description": "Generic tax document pattern",
            "priority": 0,
        },
    ],
    DocumentType.BANK_STATEMENT: [
        {
            "id": "bank_default",
            "pattern": "{Date:YYYY-MM} - {Bank Name} - Statement",
            "name": "Monthly Statement",
            "description": "Bank monthly statement",
            "priority": 0,
        },
        {
            "id": "bank_with_account",
            "pattern": "{Date:YYYY-MM} - {Bank Name} - {Last 4 Digits}",
            "name": "Statement with Account",
            "description": "Includes last 4 digits of account",
            "priority": -1,
        },
    ],
    DocumentType.INVOICE: [
        {
            "id": "invoice_default",
            "pattern": "{Date:YYYY-MM-DD} - Invoice - {Merchant} - {Amount}",
            "name": "Standard Invoice",
            "description": "Date, vendor, and amount",
            "priority": 0,
        },
    ],
    DocumentType.CONTRACT: [
        {
            "id": "contract_default",
            "pattern": "{Date:YYYY-MM-DD} - {Institution} - {Description}",
            "name": "Standard Contract",
            "description": "Date, party, and description",
            "priority": 0,
        },
    ],
    DocumentType.MEDICAL: [
        {
            "id": "medical_default",
            "pattern": "{Date:YYYY-MM-DD} - {Institution} - {Description}",
            "name": "Standard Medical",
            "description": "Date, provider, and description",
            "priority": 0,
        },
        {
            "id": "medical_eob",
            "pattern": "{Date:YYYY-MM-DD} - EOB - {Institution}",
            "name": "Explanation of Benefits",
            "description": "Insurance EOB documents",
            "match_keywords": ["eob", "explanation of benefits"],
            "priority": 10,
        },
    ],
    DocumentType.INSURANCE: [
        {
            "id": "insurance_default",
            "pattern": "{Date:YYYY} - {Institution} - {Description}",
            "name": "Standard Insurance",
            "description": "Year, insurer, and description",
            "priority": 0,
        },
        {
            "id": "insurance_policy",
            "pattern": "{Date:YYYY} - {Institution} - Policy - {Account Number}",
            "name": "Insurance Policy",
            "description": "Policy document with number",
            "match_keywords": ["policy"],
            "priority": 5,
        },
    ],
    DocumentType.INVESTMENT: [
        {
            "id": "investment_statement",
            "pattern": "{Date:YYYY-MM} - {Institution} - Statement",
            "name": "Investment Statement",
            "description": "Monthly/quarterly statement",
            "priority": 0,
        },
        {
            "id": "investment_trade",
            "pattern": "{Date:YYYY-MM-DD} - {Institution} - {Description}",
            "name": "Trade Confirmation",
            "description": "Individual trade confirmations",
            "match_keywords": ["confirmation", "trade", "buy", "sell"],
            "priority": 5,
        },
    ],
    DocumentType.PAYSLIP: [
        {
            "id": "payslip_default",
            "pattern": "{Date:YYYY-MM-DD} - {Institution} - Pay Stub",
            "name": "Standard Pay Stub",
            "description": "Pay date and employer",
            "priority": 0,
        },
    ],
    DocumentType.IDENTITY: [
        {
            "id": "identity_default",
            "pattern": "{Description} - {Date:YYYY}",
            "name": "Identity Document",
            "description": "Document type and year",
            "priority": 0,
        },
    ],
    DocumentType.CORRESPONDENCE: [
        {
            "id": "correspondence_default",
            "pattern": "{Date:YYYY-MM-DD} - {Institution} - {Description}",
            "name": "Standard Correspondence",
            "description": "Date, sender, and subject",
            "priority": 0,
        },
    ],
    DocumentType.MANUAL: [
        {
            "id": "manual_default",
            "pattern": "{Institution} - {Description} - Manual",
            "name": "Product Manual",
            "description": "Brand and product name",
            "priority": 0,
        },
    ],
    DocumentType.PHOTO: [
        {
            "id": "photo_default",
            "pattern": "{Date:YYYY-MM-DD} - {Description}",
            "name": "Standard Photo",
            "description": "Date and description",
            "priority": 0,
        },
    ],
    DocumentType.GENERAL: [
        {
            "id": "general_default",
            "pattern": "{Date:YYYY-MM-DD} - {Description}",
            "name": "General Document",
            "description": "Date and description",
            "priority": 0,
        },
    ],
}
