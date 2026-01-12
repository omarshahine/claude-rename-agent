"""Pattern management tools for the rename agent."""

from typing import Any, Optional

from ..models.document import DocumentType, DocumentInfo, PatternRule
from ..patterns.pattern_store import PatternStore
from ..patterns.default_patterns import DOCUMENT_TYPES


# Global pattern store instance
_store: Optional[PatternStore] = None


def get_store() -> PatternStore:
    """Get the global pattern store instance."""
    global _store
    if _store is None:
        _store = PatternStore()
    return _store


def set_store(store: PatternStore):
    """Set the global pattern store instance (for testing/custom data dirs)."""
    global _store
    _store = store


def list_document_types() -> list[dict[str, Any]]:
    """List all supported document types with descriptions.

    Returns:
        List of document type info dicts
    """
    result = []
    for doc_type, info in DOCUMENT_TYPES.items():
        result.append({
            "type": doc_type.value,
            "name": info["name"],
            "description": info["description"],
            "keywords": info["keywords"],
            "extract_fields": info["extract_fields"],
        })
    return result


def get_patterns(document_type: Optional[str] = None) -> list[dict[str, Any]]:
    """Get all patterns, optionally filtered by document type.

    Args:
        document_type: Optional document type to filter by

    Returns:
        List of pattern dicts
    """
    store = get_store()

    if document_type:
        doc_type = DocumentType.from_string(document_type)
        patterns = store.get_patterns_for_type(doc_type)
    else:
        patterns = store.get_all_patterns()

    return [p.to_dict() for p in patterns]


def get_pattern_for_type(
    document_type: str,
    institution: Optional[str] = None,
    keywords: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Get the best pattern for a document type.

    Args:
        document_type: The document type
        institution: Optional institution name for matching
        keywords: Optional keywords for matching

    Returns:
        The best matching pattern dict, or error
    """
    store = get_store()
    doc_type = DocumentType.from_string(document_type)

    # Create a minimal DocumentInfo for matching
    doc = DocumentInfo(
        file_path="",
        original_name="",
        document_type=doc_type,
        institution=institution,
        description=" ".join(keywords) if keywords else None,
    )

    pattern = store.get_best_pattern(doc)
    if pattern:
        return pattern.to_dict()
    else:
        return {"error": f"No pattern found for type: {document_type}"}


def add_pattern(
    document_type: str,
    pattern: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    match_keywords: Optional[list[str]] = None,
    match_institutions: Optional[list[str]] = None,
    priority: int = 5,
) -> dict[str, Any]:
    """Add a new custom pattern.

    Args:
        document_type: The document type this pattern applies to
        pattern: The pattern string with tokens like {Date:YYYY-MM-DD}
        name: Optional human-readable name
        description: Optional description
        match_keywords: Keywords that trigger this pattern
        match_institutions: Institutions that trigger this pattern
        priority: Pattern priority (higher = checked first)

    Returns:
        The created pattern dict
    """
    store = get_store()
    doc_type = DocumentType.from_string(document_type)

    rule = store.add_pattern(
        document_type=doc_type,
        pattern=pattern,
        name=name or "",
        description=description or "",
        match_keywords=match_keywords,
        match_institutions=match_institutions,
        priority=priority,
    )

    return rule.to_dict()


def update_pattern(
    pattern_id: str,
    pattern: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    match_keywords: Optional[list[str]] = None,
    match_institutions: Optional[list[str]] = None,
    priority: Optional[int] = None,
) -> dict[str, Any]:
    """Update an existing pattern.

    Args:
        pattern_id: The ID of the pattern to update
        pattern: New pattern string (optional)
        name: New name (optional)
        description: New description (optional)
        match_keywords: New keywords (optional)
        match_institutions: New institutions (optional)
        priority: New priority (optional)

    Returns:
        The updated pattern dict, or error
    """
    store = get_store()

    rule = store.update_pattern(
        pattern_id=pattern_id,
        pattern=pattern,
        name=name,
        description=description,
        match_keywords=match_keywords,
        match_institutions=match_institutions,
        priority=priority,
    )

    if rule:
        return rule.to_dict()
    else:
        return {"error": f"Pattern not found: {pattern_id}"}


def delete_pattern(pattern_id: str) -> dict[str, Any]:
    """Delete a custom pattern.

    Args:
        pattern_id: The ID of the pattern to delete

    Returns:
        Success status
    """
    store = get_store()

    if store.delete_pattern(pattern_id):
        return {"success": True, "message": f"Pattern {pattern_id} deleted"}
    else:
        return {"error": f"Could not delete pattern: {pattern_id} (not found or is a default pattern)"}


def record_pattern_usage(
    pattern_id: str,
    document_type: str,
    original_name: str,
    new_name: str,
    institution: Optional[str] = None,
) -> dict[str, Any]:
    """Record that a pattern was used (for learning).

    Args:
        pattern_id: The ID of the pattern used
        document_type: The document type
        original_name: Original filename
        new_name: New filename after renaming
        institution: Optional institution name

    Returns:
        Success status
    """
    store = get_store()

    doc = DocumentInfo(
        file_path="",
        original_name=original_name,
        document_type=DocumentType.from_string(document_type),
        institution=institution,
    )

    store.record_usage(pattern_id, doc, new_name)
    return {"success": True, "message": "Usage recorded"}


def learn_pattern(
    document_type: str,
    pattern: str,
    institution: Optional[str] = None,
) -> dict[str, Any]:
    """Learn a new pattern from batch processing.

    This creates or updates a pattern for the given type/institution combo.

    Args:
        document_type: The document type
        pattern: The pattern string to learn
        institution: Optional institution to associate with

    Returns:
        The learned pattern dict
    """
    store = get_store()
    doc_type = DocumentType.from_string(document_type)

    rule = store.learn_from_batch(doc_type, pattern, institution)
    return rule.to_dict()


def get_pattern_stats() -> dict[str, Any]:
    """Get statistics about pattern usage.

    Returns:
        Stats dict with counts by type, total patterns, etc.
    """
    store = get_store()
    return store.get_stats()


def get_rename_history(limit: int = 50) -> list[dict[str, Any]]:
    """Get recent rename history.

    Args:
        limit: Maximum number of entries to return

    Returns:
        List of history entries, most recent first
    """
    store = get_store()
    return store.get_history(limit)


def apply_pattern_to_document(
    pattern: str,
    document_info: dict[str, Any],
) -> str:
    """Apply a pattern to document info and get the resulting filename.

    Args:
        pattern: The pattern string with tokens
        document_info: Dict with document fields (date, merchant, amount, etc.)

    Returns:
        The generated filename
    """
    doc = DocumentInfo(
        file_path=document_info.get("file_path", ""),
        original_name=document_info.get("original_name", ""),
        document_type=DocumentType.from_string(document_info.get("document_type", "general")),
        date=document_info.get("date"),
        year=document_info.get("year"),
        month=document_info.get("month"),
        merchant=document_info.get("merchant"),
        amount=document_info.get("amount"),
        account_number=document_info.get("account_number"),
        form_type=document_info.get("form_type"),
        institution=document_info.get("institution"),
        description=document_info.get("description"),
    )

    # Create a temporary rule to apply the pattern
    rule = PatternRule(
        id="temp",
        document_type=doc.document_type,
        pattern=pattern,
    )

    return rule.apply_to_document(doc)
