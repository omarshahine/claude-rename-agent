"""
MCP Server for Rename Agent.

This allows Claude Code to use rename-agent tools directly.
Run with: python -m rename_agent.mcp_server
"""

import asyncio
import json
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tools.file_analyzer import (
    analyze_file,
    list_files_in_directory,
)
from .tools.pattern_manager import (
    list_document_types,
    get_patterns,
    add_pattern,
    learn_pattern,
    get_pattern_stats,
    get_rename_history,
    apply_pattern_to_document,
    set_store,
)
from .tools.file_renamer import (
    preview_rename,
    apply_rename,
    apply_batch_rename,
)
from .patterns.pattern_store import PatternStore


# Initialize pattern store
data_dir = str(Path.home() / ".rename-agent")
set_store(PatternStore(data_dir))

# Create MCP server
server = Server("rename-agent")


@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        Tool(
            name="rename_list_files",
            description="List files in a directory. Can filter by extension and scan recursively.",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory path to list"},
                    "extensions": {"type": "array", "items": {"type": "string"}, "description": "File extensions to filter (e.g., ['.pdf', '.jpg'])"},
                    "recursive": {"type": "boolean", "description": "Scan subdirectories"},
                },
                "required": ["directory"],
            },
        ),
        Tool(
            name="rename_analyze_file",
            description="Analyze a file to extract content and metadata for renaming. Works with PDFs, images, and text files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file to analyze"},
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="rename_list_document_types",
            description="List all supported document types with descriptions and keywords.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="rename_get_patterns",
            description="Get naming patterns, optionally filtered by document type.",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_type": {"type": "string", "description": "Filter by document type"},
                },
            },
        ),
        Tool(
            name="rename_add_pattern",
            description="Add a new custom naming pattern. Use tokens like {Date:YYYY-MM-DD}, {Merchant}, {Amount}, {Institution}, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_type": {"type": "string"},
                    "pattern": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "match_keywords": {"type": "array", "items": {"type": "string"}},
                    "match_institutions": {"type": "array", "items": {"type": "string"}},
                    "priority": {"type": "integer"},
                },
                "required": ["document_type", "pattern"],
            },
        ),
        Tool(
            name="rename_learn_pattern",
            description="Learn and save a pattern for future use.",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_type": {"type": "string"},
                    "pattern": {"type": "string"},
                    "institution": {"type": "string"},
                },
                "required": ["document_type", "pattern"],
            },
        ),
        Tool(
            name="rename_preview",
            description="Preview a rename operation without executing it.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "new_name": {"type": "string"},
                    "destination_dir": {"type": "string"},
                },
                "required": ["file_path", "new_name"],
            },
        ),
        Tool(
            name="rename_apply",
            description="Apply a rename operation to a file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "new_name": {"type": "string"},
                    "destination_dir": {"type": "string"},
                    "pattern_id": {"type": "string"},
                    "document_type": {"type": "string"},
                },
                "required": ["file_path", "new_name"],
            },
        ),
        Tool(
            name="rename_batch",
            description="Apply multiple rename operations at once.",
            inputSchema={
                "type": "object",
                "properties": {
                    "renames": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "file_path": {"type": "string"},
                                "new_name": {"type": "string"},
                            },
                        },
                    },
                    "destination_dir": {"type": "string"},
                    "dry_run": {"type": "boolean"},
                },
                "required": ["renames"],
            },
        ),
        Tool(
            name="rename_apply_pattern",
            description="Apply a naming pattern to document info and get the resulting filename.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Pattern with tokens like {Date}, {Merchant}"},
                    "document_info": {"type": "object", "description": "Document info with date, merchant, amount, etc."},
                },
                "required": ["pattern", "document_info"],
            },
        ),
        Tool(
            name="rename_get_history",
            description="Get recent rename history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max entries to return"},
                },
            },
        ),
        Tool(
            name="rename_get_stats",
            description="Get statistics about pattern usage.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    try:
        if name == "rename_list_files":
            result = list_files_in_directory(
                arguments.get("directory", "."),
                arguments.get("extensions"),
                arguments.get("recursive", False),
            )
        elif name == "rename_analyze_file":
            result = analyze_file(arguments["file_path"])
        elif name == "rename_list_document_types":
            result = list_document_types()
        elif name == "rename_get_patterns":
            result = get_patterns(arguments.get("document_type"))
        elif name == "rename_add_pattern":
            result = add_pattern(
                document_type=arguments.get("document_type", "general"),
                pattern=arguments.get("pattern", "{Date} - {Description}"),
                name=arguments.get("name"),
                description=arguments.get("description"),
                match_keywords=arguments.get("match_keywords"),
                match_institutions=arguments.get("match_institutions"),
                priority=arguments.get("priority", 5),
            )
        elif name == "rename_learn_pattern":
            result = learn_pattern(
                document_type=arguments.get("document_type", "general"),
                pattern=arguments.get("pattern"),
                institution=arguments.get("institution"),
            )
        elif name == "rename_preview":
            result = preview_rename(
                file_path=arguments.get("file_path"),
                new_name=arguments.get("new_name"),
                destination_dir=arguments.get("destination_dir"),
            )
        elif name == "rename_apply":
            result = apply_rename(
                file_path=arguments.get("file_path"),
                new_name=arguments.get("new_name"),
                destination_dir=arguments.get("destination_dir"),
                pattern_id=arguments.get("pattern_id"),
                document_type=arguments.get("document_type"),
            )
        elif name == "rename_batch":
            result = apply_batch_rename(
                renames=arguments.get("renames", []),
                destination_dir=arguments.get("destination_dir"),
                pattern_id=arguments.get("pattern_id"),
                document_type=arguments.get("document_type"),
                dry_run=arguments.get("dry_run", False),
            )
        elif name == "rename_apply_pattern":
            result = apply_pattern_to_document(
                pattern=arguments.get("pattern", "{Description}"),
                document_info=arguments.get("document_info", {}),
            )
        elif name == "rename_get_history":
            result = get_rename_history(arguments.get("limit", 50))
        elif name == "rename_get_stats":
            result = get_pattern_stats()
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
