"""File analysis tools for the rename agent."""

import base64
import mimetypes
import os
from pathlib import Path
from typing import Any, Optional

# Try to import optional dependencies
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


def get_mime_type(file_path: str) -> str:
    """Get the MIME type of a file."""
    if HAS_MAGIC:
        try:
            return magic.from_file(file_path, mime=True)
        except Exception:
            pass

    # Fallback to mimetypes
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"


def get_file_info(file_path: str) -> dict[str, Any]:
    """Get basic file information.

    Returns dict with:
        - name: filename
        - path: full path
        - size: file size in bytes
        - extension: file extension
        - mime_type: detected MIME type
        - is_pdf: whether it's a PDF
        - is_image: whether it's an image
    """
    path = Path(file_path)

    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    mime_type = get_mime_type(file_path)

    return {
        "name": path.name,
        "path": str(path.absolute()),
        "size": path.stat().st_size,
        "extension": path.suffix.lower(),
        "mime_type": mime_type,
        "is_pdf": mime_type == "application/pdf" or path.suffix.lower() == ".pdf",
        "is_image": mime_type.startswith("image/") if mime_type else False,
    }


def extract_pdf_text(file_path: str, max_pages: int = 3, max_chars: int = 30000) -> str:
    """Extract text from a PDF file.

    Args:
        file_path: Path to PDF file
        max_pages: Maximum number of pages to extract (3 is sufficient for renaming)
        max_chars: Maximum characters to return (default 30KB)

    Returns:
        Extracted text content
    """
    if not HAS_PYMUPDF:
        return "[PDF text extraction requires PyMuPDF. Install with: pip install pymupdf]"

    try:
        doc = fitz.open(file_path)
        text_parts = []
        total_chars = 0
        pages_shown = 0

        for page_num in range(min(len(doc), max_pages)):
            page = doc[page_num]
            page_text = page.get_text()

            # Check if we're exceeding the character limit
            if total_chars + len(page_text) > max_chars:
                remaining = max_chars - total_chars
                if remaining > 100:
                    text_parts.append(f"--- Page {page_num + 1} ---\n{page_text[:remaining]}\n[...truncated...]")
                    pages_shown += 1
                break

            text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
            total_chars += len(page_text)
            pages_shown += 1

        total_pages = len(doc)
        doc.close()

        if total_pages > pages_shown:
            text_parts.append(f"\n[Document has {total_pages} pages, showing first {pages_shown}]")

        return "\n\n".join(text_parts)
    except Exception as e:
        return f"[Error extracting PDF text: {e}]"


def extract_pdf_first_page_image(file_path: str) -> Optional[bytes]:
    """Extract the first page of a PDF as an image.

    Returns:
        PNG image bytes, or None if extraction fails
    """
    if not HAS_PYMUPDF:
        return None

    try:
        doc = fitz.open(file_path)
        page = doc[0]

        # Render at 150 DPI for good quality without huge size
        mat = fitz.Matrix(150 / 72, 150 / 72)
        pix = page.get_pixmap(matrix=mat)

        img_bytes = pix.tobytes("png")
        doc.close()
        return img_bytes
    except Exception:
        return None


def get_image_base64(file_path: str, max_size: int = 1024) -> Optional[str]:
    """Get base64-encoded image, resizing if needed.

    Args:
        file_path: Path to image file
        max_size: Maximum dimension (width or height)

    Returns:
        Base64-encoded PNG string, or None if failed
    """
    if not HAS_PIL:
        # Just read the file directly
        try:
            with open(file_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return None

    try:
        img = Image.open(file_path)

        # Resize if needed
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Convert to RGB if necessary (for PNG with transparency)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Save to bytes
        import io
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception:
        return None


def analyze_file(file_path: str) -> dict[str, Any]:
    """Analyze a file and extract content for AI processing.

    Returns a dict with:
        - file_info: basic file information
        - content_type: "text", "pdf", "image", or "binary"
        - text_content: extracted text (if applicable)
        - image_base64: base64-encoded image (if applicable)
        - analysis_ready: whether the file is ready for AI analysis
    """
    file_info = get_file_info(file_path)

    if "error" in file_info:
        return file_info

    result = {
        "file_info": file_info,
        "content_type": "binary",
        "text_content": None,
        "image_base64": None,
        "analysis_ready": False,
    }

    # Handle PDFs
    if file_info["is_pdf"]:
        result["content_type"] = "pdf"
        result["text_content"] = extract_pdf_text(file_path)

        # Also get first page as image for visual analysis
        img_bytes = extract_pdf_first_page_image(file_path)
        if img_bytes:
            result["image_base64"] = base64.b64encode(img_bytes).decode("utf-8")

        result["analysis_ready"] = True

    # Handle images
    elif file_info["is_image"]:
        result["content_type"] = "image"
        result["image_base64"] = get_image_base64(file_path)
        result["analysis_ready"] = result["image_base64"] is not None

    # Handle text files
    elif file_info["mime_type"] and file_info["mime_type"].startswith("text/"):
        result["content_type"] = "text"
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                result["text_content"] = f.read(10000)  # First 10KB
            result["analysis_ready"] = True
        except Exception as e:
            result["text_content"] = f"[Error reading file: {e}]"

    return result


def get_file_content(file_path: str) -> dict[str, Any]:
    """Get file content suitable for Claude analysis.

    This is a simplified version that returns content in a format
    that can be directly passed to Claude for analysis.
    """
    analysis = analyze_file(file_path)

    if "error" in analysis:
        return analysis

    return {
        "file_path": file_path,
        "file_name": analysis["file_info"]["name"],
        "content_type": analysis["content_type"],
        "text": analysis.get("text_content"),
        "image_base64": analysis.get("image_base64"),
        "ready": analysis["analysis_ready"],
    }


def list_files_in_directory(
    directory: str,
    extensions: Optional[list[str]] = None,
    recursive: bool = False,
) -> list[dict[str, Any]]:
    """List files in a directory with optional filtering.

    Args:
        directory: Directory path to scan
        extensions: Optional list of extensions to filter (e.g., [".pdf", ".jpg"])
        recursive: Whether to scan subdirectories

    Returns:
        List of file info dicts
    """
    path = Path(directory)

    if not path.exists():
        return [{"error": f"Directory not found: {directory}"}]

    if not path.is_dir():
        return [{"error": f"Not a directory: {directory}"}]

    files = []
    pattern = "**/*" if recursive else "*"

    for file_path in path.glob(pattern):
        if file_path.is_file():
            # Filter by extension if specified
            if extensions:
                if file_path.suffix.lower() not in [e.lower() for e in extensions]:
                    continue

            files.append(get_file_info(str(file_path)))

    # Sort by name
    files.sort(key=lambda f: f.get("name", ""))

    return files
