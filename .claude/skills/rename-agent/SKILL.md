---
name: rename-agent
description: AI-powered file renaming using the rename-agent CLI. Use when the user wants to rename files based on their content, apply consistent naming patterns, or process batches of documents. Examples include renaming tax forms, receipts, bank statements, or any documents that need organized naming.
user-invocable: true
---

# Rename Agent Skill

This skill uses the `rename-agent` CLI to intelligently rename files based on their content.

## Setup Check

First, verify rename-agent is installed:

```bash
which rename-agent
```

If not installed, help the user set it up:

```bash
pip3 install claude-rename-agent
```

Or use the install script:

```bash
curl -fsSL https://raw.githubusercontent.com/omarshahine/claude-rename-agent/main/install.sh | bash
```

Requires `ANTHROPIC_API_KEY` environment variable to be set.

## CLI Commands

```bash
# Preview files in a folder (see what would be processed)
rename-agent preview /path/to/folder

# Process files with the AI agent
rename-agent --files /path/to/documents

# Use a specific naming pattern
rename-agent --files /path/to/receipts --pattern "{Date:YYYY-MM-DD} - {Merchant}"

# Dry run (preview renames without executing)
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

## Workflow

1. When the user wants to rename files, first use `rename-agent preview` to see what files are available
2. Suggest an appropriate pattern based on the document type
3. Run with `--dry-run` first to show the user what will happen
4. Execute the rename if the user approves

## Pattern Tokens

Use these tokens in naming patterns:

| Token | Description | Example |
|-------|-------------|---------|
| `{Date:YYYY-MM-DD}` | Full date | 2024-03-15 |
| `{Date:YYYY-MM}` | Year and month | 2024-03 |
| `{Date:YYYY}` | Year only | 2024 |
| `{Year}` | Tax/fiscal year | 2024 |
| `{Merchant}` | Business/vendor name | Amazon |
| `{Amount}` | Dollar amount | 125.99 |
| `{Institution}` | Organization name | Chase Bank |
| `{Bank Name}` | Bank name | Wells Fargo |
| `{Form Type}` | Tax form type | K-1, 1099, W-2 |
| `{Account Number}` | Full account number | 1234567890 |
| `{Last 4 Digits}` | Last 4 of account | 7890 |
| `{Description}` | Document description | Annual Statement |
| `{Title}` | Document title | Q4 Report |

## Document Types

The agent recognizes:
- **Receipt** - Purchase receipts, order confirmations
- **Bill** - Utility bills, service statements
- **Tax Document** - W-2, 1099, K-1, tax returns
- **Bank Statement** - Account statements
- **Invoice** - Business invoices
- **Contract** - Legal agreements
- **Medical** - Medical records, EOBs
- **Insurance** - Policies, claims
- **Investment** - Brokerage statements
- **Payslip** - Pay stubs
- **Identity** - IDs, passports, licenses
- **Correspondence** - Letters, notices
- **Manual** - Product manuals
- **Photo** - Images, screenshots
- **General** - Other documents

## Example Usage

**User asks to rename tax documents:**
```bash
rename-agent preview ~/Downloads/tax-docs
rename-agent --files ~/Downloads/tax-docs --pattern "{Year} - {Form Type} - {Institution}" --dry-run
rename-agent --files ~/Downloads/tax-docs --pattern "{Year} - {Form Type} - {Institution}"
```

**User asks to rename receipts:**
```bash
rename-agent --files ~/Downloads/receipts --pattern "{Date:YYYY-MM-DD} - {Merchant} - {Amount}" --dry-run
```

**User wants to see what patterns have been learned:**
```bash
rename-agent patterns
```

## Data Storage

- Patterns and history stored in `~/.rename-agent/`
- Patterns are learned and remembered for future use

## Notes

- Always preview or dry-run first before executing renames
- The agent extracts text from PDFs and images to understand content
- Patterns can be learned and reused for similar documents
