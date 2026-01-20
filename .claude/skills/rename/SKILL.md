---
name: rename
description: Rename and organize files based on their content using AI-powered analysis. Use when users ask to rename files, organize documents, batch rename PDFs/images, or apply naming patterns like "{Date} - {Merchant}". Automatically checks if rename-agent is installed and helps set it up if needed.
allowed-tools: Bash, Read, Glob, Grep, Write, Edit
---

# Rename Agent Skill

This skill helps you rename and organize files based on their content using AI-powered document analysis.

## Setup Check

Before processing any files, verify the rename-agent is installed:

```bash
which rename-agent && rename-agent --version
```

### If Not Installed

If `rename-agent` is not found, help the user install it:

1. **Check Python version** (requires 3.10+):
   ```bash
   python3 --version
   ```

2. **Install via pip**:
   ```bash
   pip3 install claude-rename-agent
   ```

3. **Or use the install script**:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/omarshahine/claude-rename-agent/main/install.sh | bash
   ```

4. **Verify the API key is set**:
   ```bash
   echo $ANTHROPIC_API_KEY | head -c 10
   ```
   If not set, tell the user to set it: `export ANTHROPIC_API_KEY=your-key`

## Using Rename Agent

Once installed, use the appropriate command based on the user's request:

### Interactive Mode
```bash
rename-agent
```

### Process Files with a Prompt
```bash
rename-agent "Rename these tax documents for 2024" --files /path/to/folder
```

### Process Files with a Pattern
```bash
rename-agent --files /path/to/receipts --pattern "{Date:YYYY-MM-DD} - {Merchant}"
```

### Dry Run (Preview Only)
Add `--dry-run` to preview changes without applying them:
```bash
rename-agent --files /path/to/docs --dry-run
```

## Available Pattern Tokens

| Token | Description | Example |
|-------|-------------|---------|
| `{Date:YYYY-MM-DD}` | Full date | 2024-03-15 |
| `{Date:YYYY-MM}` | Year and month | 2024-03 |
| `{Year}` | Year only | 2024 |
| `{Merchant}` | Business/vendor name | Amazon |
| `{Amount}` | Dollar amount | 125.99 |
| `{Institution}` | Organization name | Chase Bank |
| `{Bank Name}` | Bank name | Wells Fargo |
| `{Form Type}` | Tax form type | 1099, W-2 |
| `{Account Number}` | Full account number | 1234567890 |
| `{Last 4 Digits}` | Last 4 of account | 7890 |
| `{Description}` | Document description | Annual Statement |
| `{Title}` | Document title | Q4 Report |

## Document Types Supported

Receipt, Bill, Tax Document, Bank Statement, Invoice, Contract, Medical, Insurance, Investment, Payslip, Identity, Correspondence, Manual, Photo, General

## Other Commands

```bash
# View learned patterns
rename-agent patterns

# View rename history
rename-agent history

# View statistics
rename-agent stats

# List document types
rename-agent types

# Preview files in a folder
rename-agent preview /path/to/folder --ext ".pdf,.jpg" --recursive
```

## Common Examples

### Tax Documents
```bash
rename-agent --files ~/Documents/Tax/2024 --pattern "{Year} - {Form Type} - {Institution}"
```

### Bank Statements
```bash
rename-agent --files ~/Downloads/statements --pattern "{Date:YYYY-MM} - {Bank Name} - Statement"
```

### Receipts
```bash
rename-agent --files ~/Downloads/receipts --pattern "{Date:YYYY-MM-DD} - {Merchant} - {Amount}"
```

## Troubleshooting

If you encounter issues:

1. **Command not found**: Ensure pip installed to a directory in your PATH, or run with `python3 -m rename_agent`

2. **API key errors**: Verify `ANTHROPIC_API_KEY` is set correctly

3. **PDF reading errors**: Install system dependencies:
   - macOS: `brew install libmagic`
   - Ubuntu: `sudo apt-get install libmagic1`

4. **Permission errors**: Check file permissions on the target directory
