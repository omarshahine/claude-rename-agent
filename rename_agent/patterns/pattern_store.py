"""JSON-based pattern storage with learning capabilities."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

from ..models.document import DocumentInfo, DocumentType, PatternRule
from .default_patterns import DEFAULT_PATTERNS


class PatternStore:
    """Manages naming patterns with persistence and learning."""

    def __init__(self, data_dir: Optional[str] = None):
        """Initialize the pattern store.

        Args:
            data_dir: Directory for storing pattern data. Defaults to ~/.rename-agent/
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path.home() / ".rename-agent"

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.patterns_file = self.data_dir / "patterns.json"
        self.history_file = self.data_dir / "history.json"

        self._patterns: dict[str, PatternRule] = {}
        self._history: list[dict] = []

        self._load()

    def _load(self):
        """Load patterns and history from disk."""
        # Load custom patterns
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, "r") as f:
                    data = json.load(f)
                    for pattern_data in data.get("patterns", []):
                        rule = PatternRule.from_dict(pattern_data)
                        self._patterns[rule.id] = rule
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load patterns: {e}")

        # Load history
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    self._history = json.load(f).get("history", [])
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load history: {e}")

        # Initialize with default patterns if no custom patterns exist
        self._ensure_defaults()

    def _ensure_defaults(self):
        """Ensure default patterns are available."""
        for doc_type, patterns in DEFAULT_PATTERNS.items():
            for pattern_data in patterns:
                if pattern_data["id"] not in self._patterns:
                    rule = PatternRule(
                        id=pattern_data["id"],
                        document_type=doc_type,
                        pattern=pattern_data["pattern"],
                        name=pattern_data.get("name", ""),
                        description=pattern_data.get("description", ""),
                        match_keywords=pattern_data.get("match_keywords", []),
                        match_institutions=pattern_data.get("match_institutions", []),
                        priority=pattern_data.get("priority", 0),
                        is_custom=False,
                    )
                    self._patterns[rule.id] = rule

    def _save(self):
        """Save patterns and history to disk."""
        # Save patterns
        patterns_data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "patterns": [p.to_dict() for p in self._patterns.values()],
        }
        with open(self.patterns_file, "w") as f:
            json.dump(patterns_data, f, indent=2)

        # Save history (keep last 1000 entries)
        history_data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "history": self._history[-1000:],
        }
        with open(self.history_file, "w") as f:
            json.dump(history_data, f, indent=2)

    def get_all_patterns(self) -> list[PatternRule]:
        """Get all patterns."""
        return list(self._patterns.values())

    def get_patterns_for_type(self, doc_type: DocumentType) -> list[PatternRule]:
        """Get all patterns for a document type, sorted by priority and usage."""
        patterns = [p for p in self._patterns.values() if p.document_type == doc_type]
        # Sort by priority (desc), then use_count (desc)
        patterns.sort(key=lambda p: (-p.priority, -p.use_count))
        return patterns

    def get_best_pattern(self, doc: DocumentInfo) -> Optional[PatternRule]:
        """Get the best matching pattern for a document.

        Considers:
        1. Document type match
        2. Keyword/institution matches (higher priority patterns)
        3. Usage count (more frequently used patterns preferred)
        """
        patterns = self.get_patterns_for_type(doc.document_type)

        # First, try to find a pattern with specific matches
        for pattern in patterns:
            if pattern.match_keywords or pattern.match_institutions:
                if pattern.matches_document(doc):
                    return pattern

        # Fall back to the most used general pattern
        general_patterns = [p for p in patterns if not p.match_keywords and not p.match_institutions]
        if general_patterns:
            return general_patterns[0]

        return patterns[0] if patterns else None

    def get_pattern_by_id(self, pattern_id: str) -> Optional[PatternRule]:
        """Get a specific pattern by ID."""
        return self._patterns.get(pattern_id)

    def add_pattern(
        self,
        document_type: DocumentType,
        pattern: str,
        name: str = "",
        description: str = "",
        match_keywords: Optional[list[str]] = None,
        match_institutions: Optional[list[str]] = None,
        priority: int = 5,  # Custom patterns get medium priority by default
    ) -> PatternRule:
        """Add a new custom pattern.

        Returns:
            The created PatternRule
        """
        rule = PatternRule(
            id=f"custom_{uuid.uuid4().hex[:8]}",
            document_type=document_type,
            pattern=pattern,
            name=name or f"Custom {document_type.value} Pattern",
            description=description,
            match_keywords=match_keywords or [],
            match_institutions=match_institutions or [],
            priority=priority,
            is_custom=True,
        )
        self._patterns[rule.id] = rule
        self._save()
        return rule

    def update_pattern(
        self,
        pattern_id: str,
        pattern: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        match_keywords: Optional[list[str]] = None,
        match_institutions: Optional[list[str]] = None,
        priority: Optional[int] = None,
    ) -> Optional[PatternRule]:
        """Update an existing pattern.

        Returns:
            The updated PatternRule, or None if not found
        """
        rule = self._patterns.get(pattern_id)
        if not rule:
            return None

        if pattern is not None:
            rule.pattern = pattern
        if name is not None:
            rule.name = name
        if description is not None:
            rule.description = description
        if match_keywords is not None:
            rule.match_keywords = match_keywords
        if match_institutions is not None:
            rule.match_institutions = match_institutions
        if priority is not None:
            rule.priority = priority

        self._save()
        return rule

    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern.

        Returns:
            True if deleted, False if not found or is a default pattern
        """
        rule = self._patterns.get(pattern_id)
        if not rule:
            return False

        # Don't delete default patterns, but allow marking them as low priority
        if not rule.is_custom:
            return False

        del self._patterns[pattern_id]
        self._save()
        return True

    def record_usage(self, pattern_id: str, doc: DocumentInfo, new_name: str):
        """Record that a pattern was used (for learning).

        This increases the pattern's use count and records the rename in history.
        """
        rule = self._patterns.get(pattern_id)
        if rule:
            rule.use_count += 1
            rule.last_used = datetime.now().isoformat()

        # Record in history
        self._history.append({
            "timestamp": datetime.now().isoformat(),
            "pattern_id": pattern_id,
            "document_type": doc.document_type.value,
            "original_name": doc.original_name,
            "new_name": new_name,
            "institution": doc.institution,
        })

        self._save()

    def learn_from_batch(
        self,
        doc_type: DocumentType,
        pattern: str,
        institution: Optional[str] = None,
    ) -> PatternRule:
        """Learn a new pattern from batch processing.

        If processing multiple similar documents, this creates or updates
        a pattern specifically for that type/institution combination.

        Returns:
            The learned PatternRule
        """
        # Check if we already have a pattern for this institution
        if institution:
            for rule in self._patterns.values():
                if (rule.document_type == doc_type and
                    institution.lower() in [i.lower() for i in rule.match_institutions]):
                    # Update existing pattern
                    rule.pattern = pattern
                    rule.use_count += 1
                    rule.last_used = datetime.now().isoformat()
                    self._save()
                    return rule

        # Create new pattern
        return self.add_pattern(
            document_type=doc_type,
            pattern=pattern,
            name=f"{institution or doc_type.value} Pattern",
            match_institutions=[institution] if institution else [],
            priority=10,  # Learned patterns get high priority
        )

    def get_history(self, limit: int = 50) -> list[dict]:
        """Get recent rename history."""
        return self._history[-limit:][::-1]  # Most recent first

    def get_stats(self) -> dict:
        """Get statistics about pattern usage."""
        type_counts = {}
        for rule in self._patterns.values():
            doc_type = rule.document_type.value
            if doc_type not in type_counts:
                type_counts[doc_type] = {"patterns": 0, "uses": 0}
            type_counts[doc_type]["patterns"] += 1
            type_counts[doc_type]["uses"] += rule.use_count

        return {
            "total_patterns": len(self._patterns),
            "custom_patterns": sum(1 for p in self._patterns.values() if p.is_custom),
            "total_renames": len(self._history),
            "by_type": type_counts,
        }
