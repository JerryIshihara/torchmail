"""Rich terminal output for search results."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .db import ResearchOpportunity

console = Console()


def show_banner():
    console.print(
        Panel(
            "[bold cyan]TorchMail Research Lab Search Engine[/bold cyan]\n"
            "[dim]Find top research opportunities worldwide[/dim]",
            border_style="cyan",
            padding=(1, 2),
        )
    )


def show_results(opportunities: list[ResearchOpportunity], query: str, from_cache: bool):
    source = "[green]cached[/green]" if from_cache else "[yellow]live[/yellow]"
    console.print(
        f'\n  Found [bold]{len(opportunities)}[/bold] opportunities for [italic]"{query}"[/italic]  ({source})\n'
    )

    table = Table(
        show_header=True,
        header_style="bold magenta",
        border_style="dim",
        pad_edge=True,
        expand=True,
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Researcher", min_width=20)
    table.add_column("Institution", min_width=20)
    table.add_column("Country", width=7, justify="center")
    table.add_column("Papers", width=7, justify="right")
    table.add_column("Citations", width=9, justify="right")
    table.add_column("Latest Paper", min_width=12)
    table.add_column("Score", width=7, justify="right", style="bold")

    for i, opp in enumerate(opportunities, start=1):
        prof = opp.professor
        uni_name = prof.university.name if prof and prof.university else "—"
        country = prof.university.country_code if prof and prof.university else "—"
        researcher = prof.name if prof else "—"

        latest = opp.latest_paper_date or "—"

        score_val = opp.composite_score
        if score_val >= 70:
            score_style = "green"
        elif score_val >= 40:
            score_style = "yellow"
        else:
            score_style = "red"

        table.add_row(
            str(i),
            researcher,
            _truncate(uni_name, 35),
            country or "—",
            str(opp.paper_count),
            str(opp.total_citations),
            latest,
            Text(f"{score_val:.1f}", style=score_style),
        )

    console.print(table)
    console.print()


def show_detail(opp: ResearchOpportunity, rank: int):
    prof = opp.professor
    uni = prof.university if prof else None
    lines = [
        f"[bold]Rank:[/bold] #{rank}",
        f"[bold]Researcher:[/bold] {prof.name if prof else '—'}",
        f"[bold]Institution:[/bold] {uni.name if uni else '—'}",
        f"[bold]Country:[/bold] {uni.country_code if uni else '—'}",
        f"[bold]ORCID:[/bold] {prof.orcid or '—'}" if prof else "",
        f"[bold]Papers in topic:[/bold] {opp.paper_count}",
        f"[bold]Total citations:[/bold] {opp.total_citations}",
        f"[bold]Latest paper date:[/bold] {opp.latest_paper_date or '—'}",
        f"[bold]Latest paper:[/bold] {_truncate(opp.latest_paper_title or '—', 80)}",
        f"[bold]Composite score:[/bold] {opp.composite_score:.1f}",
    ]
    console.print(Panel("\n".join(filter(None, lines)), title="Opportunity Detail", border_style="cyan"))


def _truncate(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else s[: max_len - 1] + "\u2026"
