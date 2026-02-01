"""
Rename Agent - Main agent implementation using Claude Agent SDK.

This agent specializes in analyzing documents, classifying them, and applying
consistent naming patterns that are learned over time.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from rich.style import Style

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
)

# Rich console for styled output
console = Console()

from .tools.file_analyzer import (
    analyze_file,
    get_file_content,
    list_files_in_directory,
    get_file_info,
)
from .tools.pattern_manager import (
    list_document_types,
    get_patterns,
    get_pattern_for_type,
    add_pattern,
    update_pattern,
    delete_pattern,
    learn_pattern,
    get_pattern_stats,
    get_rename_history,
    apply_pattern_to_document,
    record_pattern_usage,
    set_store,
)
from .tools.file_renamer import (
    preview_rename,
    apply_rename,
    apply_batch_rename,
    create_rename_plan,
)
from .patterns.pattern_store import PatternStore
from .models.document import DocumentType


# ============================================================================
# MCP Tool Definitions
# ============================================================================

@tool(
    "list_files",
    "List files in a directory. Can filter by extension and scan recursively. The directory parameter is REQUIRED.",
    {
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "The full path to the directory to scan. REQUIRED."
            },
            "extensions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of extensions to filter (e.g., ['.pdf', '.jpg'])"
            },
            "recursive": {
                "type": "boolean",
                "description": "Whether to scan subdirectories. Defaults to false."
            }
        },
        "required": ["directory"]
    }
)
async def tool_list_files(args: dict[str, Any]) -> dict[str, Any]:
    """List files in a directory."""
    directory = args.get("directory")
    if not directory:
        return {"content": [{"type": "text", "text": "Error: directory parameter is required"}], "is_error": True}

    extensions = args.get("extensions")
    recursive = args.get("recursive", False)

    files = list_files_in_directory(directory, extensions, recursive)

    if not files:
        return {"content": [{"type": "text", "text": f"No files found in: {directory}"}]}

    if files and "error" in files[0]:
        return {"content": [{"type": "text", "text": f"Error: {files[0]['error']}"}], "is_error": True}

    return {
        "content": [{
            "type": "text",
            "text": json.dumps(files, indent=2)
        }]
    }


@tool(
    "analyze_file",
    "Analyze a file to extract content and metadata. Works with PDFs, images, and text files. Returns first 2 pages of text for PDFs.",
    {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The full path to the file to analyze. REQUIRED."
            }
        },
        "required": ["file_path"]
    }
)
async def tool_analyze_file(args: dict[str, Any]) -> dict[str, Any]:
    """Analyze a single file."""
    file_path = args.get("file_path")
    if not file_path:
        return {"content": [{"type": "text", "text": "Error: file_path is required"}], "is_error": True}

    result = analyze_file(file_path)

    if "error" in result:
        return {"content": [{"type": "text", "text": f"Error: {result['error']}"}], "is_error": True}

    # Return text content and/or image for Claude to analyze
    content = []

    if result.get("text_content"):
        # Limit text content to avoid buffer issues (max 50KB)
        text = result["text_content"]
        if len(text) > 50000:
            text = text[:50000] + "\n\n[...truncated due to size...]"

        content.append({
            "type": "text",
            "text": f"File: {result['file_info']['name']}\nType: {result['content_type']}\n\nContent:\n{text}"
        })

    # Skip image for large files to avoid buffer issues
    file_size = result.get("file_info", {}).get("size", 0)
    if result.get("image_base64") and file_size < 5_000_000:  # Only include image if file < 5MB
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png" if result["content_type"] == "pdf" else "image/jpeg",
                "data": result["image_base64"]
            }
        })

    if not content:
        content.append({
            "type": "text",
            "text": f"File info: {json.dumps(result['file_info'], indent=2)}\n\nCould not extract content for analysis."
        })

    return {"content": content}


@tool(
    "list_document_types",
    "List all supported document types with descriptions and keywords.",
    {}
)
async def tool_list_document_types(args: dict[str, Any]) -> dict[str, Any]:
    """List document types."""
    types = list_document_types()
    return {"content": [{"type": "text", "text": json.dumps(types, indent=2)}]}


@tool(
    "get_patterns",
    "Get naming patterns, optionally filtered by document type.",
    {"document_type": str}  # Optional
)
async def tool_get_patterns(args: dict[str, Any]) -> dict[str, Any]:
    """Get patterns."""
    doc_type = args.get("document_type")
    patterns = get_patterns(doc_type)
    return {"content": [{"type": "text", "text": json.dumps(patterns, indent=2)}]}


@tool(
    "add_pattern",
    "Add a new custom naming pattern. Use tokens like {Date:YYYY-MM-DD}, {Merchant}, {Amount}, {Institution}, {Form Type}, etc.",
    {
        "document_type": str,
        "pattern": str,
        "name": str,
        "description": str,
        "match_keywords": list,
        "match_institutions": list,
        "priority": int,
    }
)
async def tool_add_pattern(args: dict[str, Any]) -> dict[str, Any]:
    """Add a new pattern."""
    result = add_pattern(
        document_type=args.get("document_type", "general"),
        pattern=args.get("pattern", "{Date} - {Description}"),
        name=args.get("name"),
        description=args.get("description"),
        match_keywords=args.get("match_keywords"),
        match_institutions=args.get("match_institutions"),
        priority=args.get("priority", 5),
    )
    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}


@tool(
    "learn_pattern",
    "Learn and save a pattern for future use. Associates it with a document type and optionally an institution.",
    {
        "document_type": str,
        "pattern": str,
        "institution": str,
    }
)
async def tool_learn_pattern(args: dict[str, Any]) -> dict[str, Any]:
    """Learn a new pattern."""
    result = learn_pattern(
        document_type=args.get("document_type", "general"),
        pattern=args.get("pattern"),
        institution=args.get("institution"),
    )
    return {"content": [{"type": "text", "text": f"Learned pattern: {json.dumps(result, indent=2)}"}]}


@tool(
    "preview_rename",
    "Preview a rename operation without executing it. Shows what the new path would be.",
    {
        "file_path": str,
        "new_name": str,
        "destination_dir": str,
    }
)
async def tool_preview_rename(args: dict[str, Any]) -> dict[str, Any]:
    """Preview rename."""
    result = preview_rename(
        file_path=args.get("file_path"),
        new_name=args.get("new_name"),
        destination_dir=args.get("destination_dir"),
    )
    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}


@tool(
    "apply_rename",
    "Apply a rename operation. Renames (and optionally moves) a file.",
    {
        "file_path": str,
        "new_name": str,
        "destination_dir": str,
        "pattern_id": str,
        "document_type": str,
    }
)
async def tool_apply_rename(args: dict[str, Any]) -> dict[str, Any]:
    """Apply rename."""
    result = apply_rename(
        file_path=args.get("file_path"),
        new_name=args.get("new_name"),
        destination_dir=args.get("destination_dir"),
        pattern_id=args.get("pattern_id"),
        document_type=args.get("document_type"),
    )
    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}


@tool(
    "apply_batch_rename",
    "Apply multiple rename operations at once. Can do a dry run first.",
    {
        "renames": list,  # List of {file_path, new_name, destination_dir?}
        "destination_dir": str,
        "pattern_id": str,
        "document_type": str,
        "dry_run": bool,
    }
)
async def tool_apply_batch_rename(args: dict[str, Any]) -> dict[str, Any]:
    """Apply batch rename."""
    result = apply_batch_rename(
        renames=args.get("renames", []),
        destination_dir=args.get("destination_dir"),
        pattern_id=args.get("pattern_id"),
        document_type=args.get("document_type"),
        dry_run=args.get("dry_run", False),
    )
    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}


@tool(
    "apply_pattern",
    "Apply a naming pattern to document info and get the resulting filename.",
    {
        "pattern": str,
        "document_info": dict,  # {date, merchant, amount, institution, etc.}
    }
)
async def tool_apply_pattern(args: dict[str, Any]) -> dict[str, Any]:
    """Apply a pattern to document info."""
    result = apply_pattern_to_document(
        pattern=args.get("pattern", "{Description}"),
        document_info=args.get("document_info", {}),
    )
    return {"content": [{"type": "text", "text": f"Generated filename: {result}"}]}


@tool(
    "get_rename_history",
    "Get recent rename history to see what patterns have been used.",
    {"limit": int}
)
async def tool_get_history(args: dict[str, Any]) -> dict[str, Any]:
    """Get rename history."""
    history = get_rename_history(args.get("limit", 50))
    return {"content": [{"type": "text", "text": json.dumps(history, indent=2)}]}


@tool(
    "get_pattern_stats",
    "Get statistics about pattern usage.",
    {}
)
async def tool_get_stats(args: dict[str, Any]) -> dict[str, Any]:
    """Get pattern stats."""
    stats = get_pattern_stats()
    return {"content": [{"type": "text", "text": json.dumps(stats, indent=2)}]}


# ============================================================================
# MCP Server Creation
# ============================================================================

def create_rename_mcp_server():
    """Create the MCP server with all rename agent tools."""
    return create_sdk_mcp_server(
        name="rename-agent",
        version="0.1.0",
        tools=[
            tool_list_files,
            tool_analyze_file,
            tool_list_document_types,
            tool_get_patterns,
            tool_add_pattern,
            tool_learn_pattern,
            tool_preview_rename,
            tool_apply_rename,
            tool_apply_batch_rename,
            tool_apply_pattern,
            tool_get_history,
            tool_get_stats,
        ]
    )


# ============================================================================
# Agent System Prompt
# ============================================================================

SYSTEM_PROMPT = """You are a specialized file renaming agent that helps users organize their documents with consistent, meaningful names.

## Your Capabilities

1. **Analyze Documents**: You can read PDFs, images, and text files to understand their content.

2. **Classify Documents**: You identify document types (receipts, bills, tax documents, bank statements, etc.) based on their content.

3. **Apply Naming Patterns**: You use pattern templates with tokens like:
   - {Date:YYYY-MM-DD} - Full date
   - {Date:YYYY-MM} - Year and month
   - {Year} - Just the year
   - {Merchant} / {Vendor} - Business name
   - {Amount} - Dollar amount
   - {Institution} / {Bank Name} / {Service Provider} - Organization name
   - {Form Type} - Tax form type (W-2, 1099, K-1, etc.)
   - {Account Number} / {Last 4 Digits} - Account identifiers
   - {Description} / {Title} / {Subject} - Document description

4. **Learn Patterns**: When you use a pattern for a batch of similar documents, you can save it for future use.

5. **Batch Processing**: You can process multiple files at once, applying consistent naming across similar documents.

## Workflow for Batch Processing

When given multiple files or a folder:

1. **List and analyze** all files to understand what you're working with
2. **Group similar files** (e.g., all K-1 forms, all Chase statements)
3. **For each group**:
   - Classify the document type
   - Check for existing patterns that match
   - If no pattern exists, suggest one and ask if it should be learned
   - Apply the pattern consistently to all files in the group
4. **Show preview** of all renames before executing
5. **Execute renames** after user confirmation
6. **Learn patterns** for future use when appropriate

## Important Guidelines

- Always **preview renames** before applying them
- Ask for **confirmation** before making changes
- When processing batches, ensure **consistent naming** within each group
- **Learn patterns** that work well so they can be reused
- Extract accurate information from documents - dates, amounts, institutions
- Use the **most specific pattern** available (e.g., K-1 pattern for K-1 forms, not generic tax pattern)

## Example Interaction

User: "Rename these K-1 tax forms for 2024"

You should:
1. List the files in the provided location
2. Analyze each file to extract: year, form type, institution name
3. Find or suggest a pattern like "{Year} - K-1 - {Institution}"
4. Generate preview names for all files
5. Show the user the proposed renames
6. After confirmation, apply the renames
7. Offer to learn this pattern for future K-1 forms from these institutions
"""


# ============================================================================
# Main Agent Functions
# ============================================================================

async def run_rename_agent(
    prompt: str,
    data_dir: Optional[str] = None,
    permission_mode: str = "default",
) -> None:
    """Run the rename agent with a given prompt.

    Args:
        prompt: The user's request
        data_dir: Optional custom directory for pattern storage
        permission_mode: Permission mode (default, acceptEdits, bypassPermissions)
    """
    # Initialize pattern store
    if data_dir:
        set_store(PatternStore(data_dir))

    # Create MCP server
    mcp_server = create_rename_mcp_server()

    # Build options
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"rename": mcp_server},
        allowed_tools=[
            # Built-in tools
            "Read",
            "Glob",
            # Custom MCP tools
            "mcp__rename__list_files",
            "mcp__rename__analyze_file",
            "mcp__rename__list_document_types",
            "mcp__rename__get_patterns",
            "mcp__rename__add_pattern",
            "mcp__rename__learn_pattern",
            "mcp__rename__preview_rename",
            "mcp__rename__apply_rename",
            "mcp__rename__apply_batch_rename",
            "mcp__rename__apply_pattern",
            "mcp__rename__get_rename_history",
            "mcp__rename__get_pattern_stats",
        ],
        permission_mode=permission_mode,
        max_buffer_size=5 * 1024 * 1024,  # 5MB buffer for large files
    )

    # Run the agent using ClaudeSDKClient (required for MCP server support)
    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        # Render markdown for rich text output
                        console.print(Markdown(block.text))
                    elif isinstance(block, ToolUseBlock):
                        # Styled tool usage indicator
                        tool_name = block.name.replace("mcp__rename__", "")
                        console.print(f"  [dim]●[/dim] [green]{tool_name}[/green]", end=" ")


async def run_interactive_session(
    data_dir: Optional[str] = None,
    permission_mode: str = "default",
) -> None:
    """Run an interactive rename agent session.

    Args:
        data_dir: Optional custom directory for pattern storage
        permission_mode: Permission mode
    """
    # Initialize pattern store
    if data_dir:
        set_store(PatternStore(data_dir))

    # Create MCP server
    mcp_server = create_rename_mcp_server()

    # Build options
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"rename": mcp_server},
        allowed_tools=[
            "Read",
            "Glob",
            "mcp__rename__list_files",
            "mcp__rename__analyze_file",
            "mcp__rename__list_document_types",
            "mcp__rename__get_patterns",
            "mcp__rename__add_pattern",
            "mcp__rename__learn_pattern",
            "mcp__rename__preview_rename",
            "mcp__rename__apply_rename",
            "mcp__rename__apply_batch_rename",
            "mcp__rename__apply_pattern",
            "mcp__rename__get_rename_history",
            "mcp__rename__get_pattern_stats",
        ],
        permission_mode=permission_mode,
        max_buffer_size=5 * 1024 * 1024,  # 5MB buffer for large files
    )

    async with ClaudeSDKClient(options=options) as client:
        while True:
            try:
                # Styled prompt
                console.print()
                user_input = console.input("[green]>[/green] ").strip()

                # Handle commands
                if user_input.lower() in ("quit", "exit", "q", "/quit", "/exit"):
                    console.print()
                    console.print("[dim]Goodbye![/dim]")
                    break

                if user_input.lower() in ("/help", "help"):
                    console.print()
                    console.print("  [dim]Commands:[/dim]")
                    console.print("    [green]/stats[/green]   - Show pattern statistics")
                    console.print("    [green]/history[/green] - Show rename history")
                    console.print("    [green]/quit[/green]    - Exit the agent")
                    continue

                if not user_input:
                    continue

                await client.query(user_input)

                console.print()
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                # Render markdown for rich text
                                console.print(Markdown(block.text))
                            elif isinstance(block, ToolUseBlock):
                                # Styled tool usage indicator
                                tool_name = block.name.replace("mcp__rename__", "")
                                console.print(f"  [dim]●[/dim] [green]{tool_name}[/green]", end=" ")

            except KeyboardInterrupt:
                console.print()
                console.print("[dim]Interrupted. Type /quit to exit.[/dim]")
            except Exception as e:
                console.print(f"\n[red]Error:[/red] {e}")


def main():
    """Entry point for running the agent."""
    import sys

    if len(sys.argv) > 1:
        # Run with command line prompt
        prompt = " ".join(sys.argv[1:])
        asyncio.run(run_rename_agent(prompt))
    else:
        # Run interactive session
        asyncio.run(run_interactive_session())


if __name__ == "__main__":
    main()
