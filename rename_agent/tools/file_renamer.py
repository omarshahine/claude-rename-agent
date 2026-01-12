"""File renaming tools for the rename agent."""

import os
import shutil
from pathlib import Path
from typing import Any, Optional

from ..models.document import DocumentType, DocumentInfo, RenameResult, PatternRule
from ..patterns.pattern_store import PatternStore
from .pattern_manager import get_store


def sanitize_filename(name: str) -> str:
    """Sanitize a filename by removing/replacing invalid characters.

    Args:
        name: The proposed filename

    Returns:
        A valid filename
    """
    # Characters not allowed in filenames (Windows is most restrictive)
    invalid_chars = '<>:"/\\|?*'

    result = name
    for char in invalid_chars:
        result = result.replace(char, '-')

    # Remove leading/trailing whitespace and dots
    result = result.strip().strip('.')

    # Collapse multiple spaces/dashes
    import re
    result = re.sub(r'\s+', ' ', result)
    result = re.sub(r'-+', '-', result)
    result = re.sub(r'\s*-\s*', ' - ', result)

    # Ensure the filename isn't empty
    if not result:
        result = "unnamed"

    return result


def get_unique_path(file_path: Path) -> Path:
    """Get a unique path if the file already exists.

    Args:
        file_path: The proposed file path

    Returns:
        A path that doesn't exist (may have number suffix)
    """
    if not file_path.exists():
        return file_path

    base = file_path.stem
    ext = file_path.suffix
    parent = file_path.parent

    counter = 1
    while True:
        new_path = parent / f"{base} ({counter}){ext}"
        if not new_path.exists():
            return new_path
        counter += 1
        if counter > 1000:  # Safety limit
            raise ValueError("Could not find unique filename")


def preview_rename(
    file_path: str,
    new_name: str,
    destination_dir: Optional[str] = None,
) -> dict[str, Any]:
    """Preview a rename operation without executing it.

    Args:
        file_path: Path to the file to rename
        new_name: The new filename (without extension)
        destination_dir: Optional destination directory (moves file if specified)

    Returns:
        Preview dict with original and new paths
    """
    source = Path(file_path)

    if not source.exists():
        return {"error": f"File not found: {file_path}"}

    # Sanitize the new name
    clean_name = sanitize_filename(new_name)

    # Keep the original extension
    ext = source.suffix
    new_filename = f"{clean_name}{ext}"

    # Determine destination
    if destination_dir:
        dest_path = Path(destination_dir)
        if not dest_path.exists():
            return {"error": f"Destination directory not found: {destination_dir}"}
        new_path = dest_path / new_filename
    else:
        new_path = source.parent / new_filename

    # Check for conflicts
    unique_path = get_unique_path(new_path)
    has_conflict = unique_path != new_path

    return {
        "original_path": str(source),
        "original_name": source.name,
        "new_name": new_filename,
        "new_path": str(unique_path),
        "will_move": destination_dir is not None,
        "has_conflict": has_conflict,
        "conflict_resolution": str(unique_path) if has_conflict else None,
    }


def apply_rename(
    file_path: str,
    new_name: str,
    destination_dir: Optional[str] = None,
    pattern_id: Optional[str] = None,
    document_type: Optional[str] = None,
) -> dict[str, Any]:
    """Apply a rename operation.

    Args:
        file_path: Path to the file to rename
        new_name: The new filename (without extension)
        destination_dir: Optional destination directory (moves file if specified)
        pattern_id: Optional pattern ID to record usage
        document_type: Optional document type for history

    Returns:
        Result dict with success status and paths
    """
    preview = preview_rename(file_path, new_name, destination_dir)

    if "error" in preview:
        return preview

    source = Path(file_path)
    dest = Path(preview["new_path"])

    try:
        # Create destination directory if needed
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Perform the rename/move
        shutil.move(str(source), str(dest))

        # Record pattern usage if specified
        if pattern_id:
            store = get_store()
            doc_type = DocumentType.from_string(document_type or "general")
            doc = DocumentInfo(
                file_path=file_path,
                original_name=source.name,
                document_type=doc_type,
            )
            store.record_usage(pattern_id, doc, dest.name)

        return {
            "success": True,
            "original_path": str(source),
            "original_name": source.name,
            "new_name": dest.name,
            "new_path": str(dest),
            "was_moved": preview["will_move"],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "original_path": str(source),
        }


def apply_batch_rename(
    renames: list[dict[str, Any]],
    destination_dir: Optional[str] = None,
    pattern_id: Optional[str] = None,
    document_type: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Apply multiple rename operations.

    Args:
        renames: List of dicts with 'file_path' and 'new_name' keys
        destination_dir: Optional shared destination directory
        pattern_id: Optional pattern ID to record usage for all
        document_type: Optional document type for history
        dry_run: If True, only preview without executing

    Returns:
        Results dict with success count, failures, and details
    """
    results = []
    success_count = 0
    failure_count = 0

    for rename in renames:
        file_path = rename.get("file_path")
        new_name = rename.get("new_name")

        if not file_path or not new_name:
            results.append({
                "success": False,
                "error": "Missing file_path or new_name",
                "original": rename,
            })
            failure_count += 1
            continue

        # Use per-file destination if specified, otherwise use shared
        dest = rename.get("destination_dir", destination_dir)

        if dry_run:
            preview = preview_rename(file_path, new_name, dest)
            preview["dry_run"] = True
            results.append(preview)
            if "error" not in preview:
                success_count += 1
            else:
                failure_count += 1
        else:
            result = apply_rename(
                file_path,
                new_name,
                dest,
                pattern_id=pattern_id,
                document_type=document_type,
            )
            results.append(result)
            if result.get("success"):
                success_count += 1
            else:
                failure_count += 1

    return {
        "total": len(renames),
        "success_count": success_count,
        "failure_count": failure_count,
        "dry_run": dry_run,
        "results": results,
    }


def create_rename_plan(
    files: list[str],
    pattern: str,
    document_infos: list[dict[str, Any]],
    destination_dir: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Create a rename plan for multiple files using a pattern.

    Args:
        files: List of file paths
        pattern: The naming pattern to apply
        document_infos: List of document info dicts (matching order of files)
        destination_dir: Optional shared destination

    Returns:
        List of rename plan entries
    """
    if len(files) != len(document_infos):
        return [{"error": "files and document_infos must have same length"}]

    plan = []

    for file_path, doc_info in zip(files, document_infos):
        # Create DocumentInfo from dict
        doc = DocumentInfo(
            file_path=file_path,
            original_name=Path(file_path).name,
            document_type=DocumentType.from_string(doc_info.get("document_type", "general")),
            date=doc_info.get("date"),
            year=doc_info.get("year"),
            month=doc_info.get("month"),
            merchant=doc_info.get("merchant"),
            amount=doc_info.get("amount"),
            account_number=doc_info.get("account_number"),
            form_type=doc_info.get("form_type"),
            institution=doc_info.get("institution"),
            description=doc_info.get("description"),
        )

        # Create a temporary rule to apply the pattern
        rule = PatternRule(
            id="temp",
            document_type=doc.document_type,
            pattern=pattern,
        )

        new_name = rule.apply_to_document(doc)

        # Get preview
        preview = preview_rename(file_path, new_name, destination_dir)
        preview["document_info"] = doc_info
        preview["pattern_used"] = pattern

        plan.append(preview)

    return plan
