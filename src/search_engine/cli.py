"""CLI entry point for the TorchMail search engine MVP."""

from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import cache, config, display
from .db import get_session, init_db
from .search import fetch_opportunities

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """TorchMail Research Lab Search Engine — MVP CLI"""
    if ctx.invoked_subcommand is None:
        ctx.invoke(interactive)


@main.command()
@click.argument("query", required=False)
def search(query: str | None):
    """Search for research opportunities by topic.

    Example: search "bio-engineering in genome analysis"
    """
    init_db()
    if not query:
        query = console.input("[bold cyan]Enter research area:[/bold cyan] ").strip()
    if not query:
        console.print("[red]Empty query — aborting.[/red]")
        raise SystemExit(1)
    _run_search(query)


@main.command()
def interactive():
    """Interactive search loop (default mode)."""
    display.show_banner()
    init_db()
    console.print("  Type a research area to search, or [bold]quit[/bold] to exit.\n")

    while True:
        try:
            query = console.input("[bold cyan]Search>[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nBye!")
            break
        if not query or query.lower() in ("quit", "exit", "q"):
            console.print("Bye!")
            break
        _run_search(query)


@main.command()
def stats():
    """Show database statistics."""
    init_db()
    session = get_session()
    from .db import Professor, ResearchOpportunity, SearchCache, University

    console.print(Panel(
        f"Universities: {session.query(University).count()}\n"
        f"Professors:   {session.query(Professor).count()}\n"
        f"Opportunities:{session.query(ResearchOpportunity).count()}\n"
        f"Cache entries: {session.query(SearchCache).count()}",
        title="Database Stats",
        border_style="cyan",
    ))
    session.close()


def _run_search(query: str):
    session = get_session()
    try:
        cached = cache.lookup(session, query)
        if cached:
            display.show_results(cached, query, from_cache=True)
            _offer_detail(cached)
            return

        console.print(f"\n  Fetching from OpenAlex API ({config.OPENALEX_PAGES_TO_FETCH} pages)…")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Searching…", total=config.OPENALEX_PAGES_TO_FETCH)

            def on_progress(page, total):
                progress.update(task, advance=1, description=f"Page {page}/{total}")

            authors = fetch_opportunities(query, on_progress=on_progress)

        if not authors:
            console.print("[yellow]  No results found. Try a different query.[/yellow]\n")
            return

        opportunities = cache.store(session, query, authors)
        display.show_results(opportunities, query, from_cache=False)
        _offer_detail(opportunities)

    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise
    finally:
        session.close()


def _offer_detail(opportunities):
    """Let the user drill into a specific result."""
    while True:
        ans = console.input("  [dim]Enter rank # for details (or press Enter to continue):[/dim] ").strip()
        if not ans:
            break
        try:
            idx = int(ans)
            if 1 <= idx <= len(opportunities):
                display.show_detail(opportunities[idx - 1], idx)
            else:
                console.print(f"  [yellow]Pick a number between 1 and {len(opportunities)}[/yellow]")
        except ValueError:
            break


