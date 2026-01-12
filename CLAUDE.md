# Rename Agent

An AI-powered file renaming agent built with the Claude Agent SDK.

## Project Overview

This agent analyzes documents (PDFs, images, text files), classifies them by type, and applies consistent naming patterns. It learns patterns over time for reuse.

## Key Files

- `rename_agent/agent.py` - Main agent with MCP tools and system prompt
- `rename_agent/cli.py` - Typer CLI interface
- `rename_agent/models/document.py` - Data models (DocumentType, DocumentInfo, PatternRule)
- `rename_agent/patterns/pattern_store.py` - JSON persistence for patterns and history
- `rename_agent/patterns/default_patterns.py` - Default naming patterns per document type
- `rename_agent/tools/file_analyzer.py` - PDF/image content extraction
- `rename_agent/tools/pattern_manager.py` - Pattern CRUD operations
- `rename_agent/tools/file_renamer.py` - File rename operations

## Running the Agent

```bash
# Interactive mode
rename-agent

# Process a folder
rename-agent --files /path/to/documents

# With a specific pattern
rename-agent --files /path/to/receipts --pattern "{Date:YYYY-MM-DD} - {Merchant}"

# Dry run
rename-agent --files /path/to/docs --dry-run
```

## Architecture

The agent uses:
- **Claude Agent SDK** - For the agent loop and built-in tools
- **Custom MCP Tools** - For file analysis, pattern management, and renaming
- **JSON Storage** - Patterns and history stored in `~/.rename-agent/`

## Document Types

Receipt, Bill, Tax Document, Bank Statement, Invoice, Contract, Medical, Insurance, Investment, Payslip, Identity, Correspondence, Manual, Photo, General

## Pattern Tokens

`{Date:YYYY-MM-DD}`, `{Year}`, `{Merchant}`, `{Amount}`, `{Institution}`, `{Form Type}`, `{Account Number}`, `{Last 4 Digits}`, `{Description}`, `{Title}`

## Development

```bash
# Install
pip3.11 install -e .

# Run tests
python3.11 -m pytest
```

## Dependencies

- Python 3.10+
- claude-agent-sdk
- pymupdf (PDF extraction)
- pillow (image processing)
- python-magic (file type detection)
- rich, typer (CLI)
