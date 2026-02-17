# Rename Agent

An AI-powered file renaming agent that analyzes documents, classifies them, and applies consistent naming patterns.

## Quick Reference

```bash
# Install
pip3.11 install -e .

# Run tests
python3.11 -m pytest
```

## CLI Usage

```bash
# Interactive mode
rename-agent

# Process files with AI
rename-agent --files /path/to/documents

# Use a specific naming pattern
rename-agent --files /path/to/receipts --pattern "{Date:YYYY-MM-DD} - {Merchant}"

# Dry run (preview without renaming)
rename-agent --files /path/to/docs --dry-run

# Preview files in a folder
rename-agent preview /path/to/folder

# View learned patterns / history / stats
rename-agent patterns
rename-agent history
rename-agent stats

# List supported document types
rename-agent types
```

## Architecture

The agent uses:
- **Claude Agent SDK** — Agent loop with built-in tools
- **Custom MCP Tools** — File analysis, pattern management, renaming
- **JSON Storage** — Patterns and history in `~/.rename-agent/`

### Key Files

| File | Purpose |
|------|---------|
| `rename_agent/agent.py` | Main agent with MCP tools and system prompt |
| `rename_agent/cli.py` | Typer CLI interface |
| `rename_agent/models/document.py` | Data models (DocumentType, DocumentInfo, PatternRule) |
| `rename_agent/patterns/pattern_store.py` | JSON persistence for patterns and history |
| `rename_agent/patterns/default_patterns.py` | Default naming patterns per document type |
| `rename_agent/tools/file_analyzer.py` | PDF/image content extraction |
| `rename_agent/tools/pattern_manager.py` | Pattern CRUD operations |
| `rename_agent/tools/file_renamer.py` | File rename operations |

## Pattern Tokens

| Token | Example |
|-------|---------|
| `{Date:YYYY-MM-DD}` | 2024-03-15 |
| `{Date:YYYY-MM}` | 2024-03 |
| `{Year}` | 2024 |
| `{Merchant}` | Business/vendor name |
| `{Amount}` | Dollar amount |
| `{Institution}` | Organization name |
| `{Bank Name}` | Bank name |
| `{Form Type}` | 1099, W-2, K-1 |
| `{Account Number}` | Full account number |
| `{Last 4 Digits}` | Last 4 of account |
| `{Description}` | Document description |
| `{Title}` | Document title |

## Document Types

Receipt, Bill, Tax Document, Bank Statement, Invoice, Contract, Medical, Insurance, Investment, Payslip, Identity, Correspondence, Manual, Photo, General

## Dependencies

- Python 3.10+
- claude-agent-sdk
- pymupdf (PDF extraction)
- pillow (image processing)
- python-magic (file type detection)
- rich, typer (CLI)

## Code Hygiene

- No hardcoded user paths (`/Users/[name]/`) - use `~/` or `${HOME}`
- No personal email addresses in tracked files (allowed: `@example.com`, `@anthropic.com`, `@noreply`)
- No API keys or secrets in code - use environment variables
- No phone numbers or PII in examples - use generic placeholders
