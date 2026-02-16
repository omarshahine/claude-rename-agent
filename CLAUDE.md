# Rename Agent

An AI-powered file renaming agent that analyzes documents, classifies them, and applies consistent naming patterns.

## When to Use

Use rename-agent when users ask to:
- Rename files based on their content
- Organize documents with consistent naming
- Process batches of PDFs, images, or text files
- Apply naming patterns like `{Date} - {Merchant}` or `{Year} - {Form Type}`

## Commands

```bash
# Preview files in a folder
rename-agent preview /path/to/folder

# Process files with the AI agent
rename-agent --files /path/to/documents

# Use a specific naming pattern
rename-agent --files /path/to/receipts --pattern "{Date:YYYY-MM-DD} - {Merchant}"

# Dry run (preview without renaming)
rename-agent --files /path/to/docs --dry-run

# View learned patterns
rename-agent patterns

# View rename history
rename-agent history

# View statistics
rename-agent stats

# List supported document types
rename-agent types
```

## Pattern Tokens

Available tokens for naming patterns:
- `{Date:YYYY-MM-DD}` - Full date (2024-03-15)
- `{Date:YYYY-MM}` - Year and month (2024-03)
- `{Date:YYYY}` or `{Year}` - Year only (2024)
- `{Merchant}` - Business/vendor name
- `{Amount}` - Dollar amount
- `{Institution}` - Organization name
- `{Bank Name}` - Bank name
- `{Form Type}` - Tax form type (1099, W-2, K-1)
- `{Account Number}` - Full account number
- `{Last 4 Digits}` - Last 4 of account
- `{Description}` - Document description
- `{Title}` - Document title

## Document Types

Receipt, Bill, Tax Document, Bank Statement, Invoice, Contract, Medical, Insurance, Investment, Payslip, Identity, Correspondence, Manual, Photo, General

## Data Storage

Patterns and history are stored in `~/.rename-agent/`

---

# Development

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

## Code Hygiene

- No hardcoded user paths (`/Users/[name]/`) - use `~/` or `${HOME}`
- No personal email addresses in tracked files (allowed: `@example.com`, `@anthropic.com`, `@noreply`)
- No API keys or secrets in code - use environment variables
- No phone numbers or PII in examples - use generic placeholders

## Dependencies

- Python 3.10+
- claude-agent-sdk
- pymupdf (PDF extraction)
- pillow (image processing)
- python-magic (file type detection)
- rich, typer (CLI)
## Claude Code GitHub Actions

This repo uses Claude Code GitHub Actions for PR automation:

- **`claude-code-review.yml`** - Auto-reviews PRs when marked "Ready for review" (draft → ready triggers review)
- **`claude.yml`** - Responds to `@claude` mentions in PR/issue comments for manual reviews

**Workflow:** Open PRs as draft → push commits → mark "Ready for review" to trigger auto-review. Use `@claude` in comments for follow-up reviews.
