"""
CLI interface for the Rename Agent.

Usage:
    rename-agent                        # Interactive mode
    rename-agent "rename these files"   # Single prompt
    rename-agent --files /path/to/files # Process files/folder
    rename-agent --stats                # Show pattern statistics
    rename-agent --history              # Show rename history
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.style import Style

from .agent import run_rename_agent, run_interactive_session
from .tools.pattern_manager import (
    get_patterns,
    get_pattern_stats,
    get_rename_history,
    list_document_types,
    set_store,
)
from .tools.file_analyzer import list_files_in_directory
from .patterns.pattern_store import PatternStore

app = typer.Typer(
    name="rename-agent",
    help="AI-powered file renaming agent with pattern learning",
    add_completion=False,
)
console = Console()

# Branding colors (Claude-like green accent)
ACCENT_COLOR = "green"
DIM_COLOR = "dim"

BANNER = r"""
  ██████╗ ███████╗███╗   ██╗ █████╗ ███╗   ███╗███████╗
  ██╔══██╗██╔════╝████╗  ██║██╔══██╗████╗ ████║██╔════╝
  ██████╔╝█████╗  ██╔██╗ ██║███████║██╔████╔██║█████╗
  ██╔══██╗██╔══╝  ██║╚██╗██║██╔══██║██║╚██╔╝██║██╔══╝
  ██║  ██║███████╗██║ ╚████║██║  ██║██║ ╚═╝ ██║███████╗
  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝
                       AGENT

  AI-powered file renaming with pattern learning
"""


def print_banner():
    """Print the styled welcome banner."""
    console.print()
    # Split and skip empty first/last lines, but preserve indentation
    lines = BANNER.split('\n')
    for line in lines[1:-1]:  # Skip first empty line and last empty line
        console.print(Text(line, style=Style(color="green")))
    console.print("  " + "─" * 54, style="dim")


def print_help_hint():
    """Print helpful hints for the user."""
    console.print()
    console.print(f"  [dim]Type your request, or try:[/dim]")
    console.print(f"    [green]•[/green] [white]Rename these files in ~/Downloads[/white]")
    console.print(f"    [green]•[/green] [white]Process my tax documents with pattern {{Year}} - {{Form Type}}[/white]")
    console.print(f"    [green]•[/green] [white]Show me what patterns I have saved[/white]")
    console.print()
    console.print(f"  [dim]Commands: [green]/help[/green] [green]/stats[/green] [green]/history[/green] [green]/quit[/green][/dim]")
    console.print()


def get_data_dir(data_dir: Optional[str] = None) -> str:
    """Get the data directory path."""
    if data_dir:
        return data_dir
    return str(Path.home() / ".rename-agent")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    prompt: Optional[str] = typer.Argument(
        None,
        help="The renaming task to perform. If not provided, starts interactive mode.",
    ),
    files: Optional[Path] = typer.Option(
        None,
        "--files", "-f",
        help="Path to file(s) or folder to process",
        exists=True,
    ),
    pattern: Optional[str] = typer.Option(
        None,
        "--pattern", "-p",
        help="Naming pattern to use (e.g., '{Date:YYYY} - {Form Type} - {Institution}')",
    ),
    document_type: Optional[str] = typer.Option(
        None,
        "--type", "-t",
        help="Document type (receipt, bill, tax_document, bank_statement, etc.)",
    ),
    data_dir: Optional[str] = typer.Option(
        None,
        "--data-dir", "-d",
        help="Custom directory for storing patterns and history",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview renames without executing them",
    ),
    auto_approve: bool = typer.Option(
        False,
        "--yes", "-y",
        help="Auto-approve all rename operations",
    ),
):
    """
    AI-powered file renaming with pattern learning.

    Run without arguments for interactive mode, or provide a prompt/files to process.

    Examples:

        rename-agent

        rename-agent "Rename these 1099 tax forms" --files /path/to/forms

        rename-agent --files /path/to/receipts --pattern "{Date:YYYY-MM-DD} - {Merchant}"

        rename-agent stats
    """
    # If a subcommand was invoked, don't run main
    if ctx.invoked_subcommand is not None:
        return

    # Initialize data directory
    data_path = get_data_dir(data_dir)
    set_store(PatternStore(data_path))

    # Build the prompt based on options
    if files:
        file_path = str(files.absolute())
        if files.is_dir():
            base_prompt = f"Process all files in the folder: {file_path}"
        else:
            base_prompt = f"Process this file: {file_path}"

        if pattern:
            base_prompt += f"\n\nUse this naming pattern: {pattern}"

        if document_type:
            base_prompt += f"\n\nDocument type: {document_type}"

        if dry_run:
            base_prompt += "\n\nThis is a dry run - show me what would be renamed but don't execute."

        if prompt:
            base_prompt = f"{prompt}\n\n{base_prompt}"

        prompt = base_prompt

    # Determine permission mode
    permission_mode = "bypassPermissions" if auto_approve else "default"

    if prompt:
        # Run with the provided prompt
        console.print()
        console.print(f"  [green]>[/green] [bold]{prompt}[/bold]")
        console.print()
        asyncio.run(run_rename_agent(prompt, data_path, permission_mode))
    else:
        # Interactive mode
        print_banner()
        print_help_hint()
        asyncio.run(run_interactive_session(data_path, permission_mode))


@app.command()
def stats(
    data_dir: Optional[str] = typer.Option(
        None,
        "--data-dir", "-d",
        help="Custom data directory",
    ),
):
    """Show pattern usage statistics."""
    data_path = get_data_dir(data_dir)
    set_store(PatternStore(data_path))

    stats_data = get_pattern_stats()

    console.print(Panel(
        f"[bold]Total Patterns:[/bold] {stats_data['total_patterns']}\n"
        f"[bold]Custom Patterns:[/bold] {stats_data['custom_patterns']}\n"
        f"[bold]Total Renames:[/bold] {stats_data['total_renames']}",
        title="Pattern Statistics",
    ))

    if stats_data.get("by_type"):
        table = Table(title="Usage by Document Type")
        table.add_column("Type", style="cyan")
        table.add_column("Patterns", justify="right")
        table.add_column("Uses", justify="right")

        for doc_type, counts in sorted(stats_data["by_type"].items()):
            table.add_row(
                doc_type,
                str(counts["patterns"]),
                str(counts["uses"]),
            )

        console.print(table)


@app.command()
def history(
    limit: int = typer.Option(
        20,
        "--limit", "-n",
        help="Number of entries to show",
    ),
    data_dir: Optional[str] = typer.Option(
        None,
        "--data-dir", "-d",
        help="Custom data directory",
    ),
):
    """Show recent rename history."""
    data_path = get_data_dir(data_dir)
    set_store(PatternStore(data_path))

    history_data = get_rename_history(limit)

    if not history_data:
        console.print("[yellow]No rename history found.[/yellow]")
        return

    table = Table(title=f"Recent Renames (last {len(history_data)})")
    table.add_column("Date", style="dim")
    table.add_column("Type", style="cyan")
    table.add_column("Original", style="red")
    table.add_column("New Name", style="green")

    for entry in history_data:
        timestamp = entry.get("timestamp", "")[:10]
        doc_type = entry.get("document_type", "")
        original = entry.get("original_name", "")[:30]
        new_name = entry.get("new_name", "")[:40]

        table.add_row(timestamp, doc_type, original, new_name)

    console.print(table)


@app.command()
def patterns(
    document_type: Optional[str] = typer.Option(
        None,
        "--type", "-t",
        help="Filter by document type",
    ),
    data_dir: Optional[str] = typer.Option(
        None,
        "--data-dir", "-d",
        help="Custom data directory",
    ),
):
    """List available naming patterns."""
    data_path = get_data_dir(data_dir)
    set_store(PatternStore(data_path))

    patterns_data = get_patterns(document_type)

    if not patterns_data:
        console.print("[yellow]No patterns found.[/yellow]")
        return

    table = Table(title="Naming Patterns")
    table.add_column("ID", style="dim", max_width=20)
    table.add_column("Type", style="cyan")
    table.add_column("Pattern", style="green")
    table.add_column("Uses", justify="right")
    table.add_column("Custom", justify="center")

    for p in patterns_data:
        table.add_row(
            p["id"][:18],
            p["document_type"],
            p["pattern"],
            str(p["use_count"]),
            "✓" if p.get("is_custom") else "",
        )

    console.print(table)


@app.command()
def types():
    """List supported document types."""
    types_data = list_document_types()

    table = Table(title="Supported Document Types")
    table.add_column("Type", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Description")

    for t in types_data:
        table.add_row(
            t["type"],
            t["name"],
            t["description"][:50] + "..." if len(t["description"]) > 50 else t["description"],
        )

    console.print(table)


@app.command()
def preview(
    files: Path = typer.Argument(
        ...,
        help="Path to file(s) or folder to preview",
        exists=True,
    ),
    extensions: Optional[str] = typer.Option(
        None,
        "--ext", "-e",
        help="File extensions to include (comma-separated, e.g., '.pdf,.jpg')",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive", "-r",
        help="Scan subdirectories",
    ),
):
    """Preview files that would be processed."""
    file_path = str(files.absolute())

    if files.is_file():
        file_list = [{"name": files.name, "path": file_path, "size": files.stat().st_size}]
    else:
        ext_list = [e.strip() for e in extensions.split(",")] if extensions else None
        file_list = list_files_in_directory(file_path, ext_list, recursive)

    if not file_list or (len(file_list) == 1 and "error" in file_list[0]):
        console.print(f"[red]Error: {file_list[0].get('error', 'No files found')}[/red]")
        return

    table = Table(title=f"Files in {file_path}")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="dim")
    table.add_column("Size", justify="right")

    for f in file_list:
        size = f.get("size", 0)
        size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
        table.add_row(
            f.get("name", "")[:50],
            f.get("extension", ""),
            size_str,
        )

    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {len(file_list)} files")


if __name__ == "__main__":
    app()
