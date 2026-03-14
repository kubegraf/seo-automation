#!/usr/bin/env python3
"""
Full SEO Pipeline Orchestrator
Runs all pipeline steps in sequence.
"""
import os
import sys
import logging
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)
console = Console()


def run_step(name: str, func) -> bool:
    """Run a pipeline step with error handling."""
    console.print(f"\n{'='*60}")
    try:
        func()
        return True
    except Exception as e:
        console.print(f"[red]❌ Step '{name}' failed: {e}[/red]")
        logger.exception(f"Pipeline step '{name}' failed")
        return False


def main():
    start_time = datetime.utcnow()
    console.print(Panel.fit(
        "[bold blue]🤖 Kubegraf SEO Automation Pipeline[/bold blue]\n"
        f"Started: {start_time.strftime('%Y-%m-%d %H:%M UTC')}",
        border_style="blue"
    ))

    # Check required env
    if not os.environ.get("GEMINI_API_KEY"):
        console.print("[red]❌ GEMINI_API_KEY environment variable not set![/red]")
        sys.exit(1)

    steps = []

    # Determine which steps to run
    run_all = os.environ.get("PIPELINE_STEP", "all") == "all"
    step_arg = os.environ.get("PIPELINE_STEP", "all")

    if run_all or step_arg == "keyword_discovery":
        from pipeline import keyword_discovery
        steps.append(("Keyword Discovery", keyword_discovery.run))

    if run_all or step_arg == "competitor_analysis":
        from pipeline import competitor_analysis
        steps.append(("Competitor Analysis", competitor_analysis.run))

    if run_all or step_arg == "content_generation":
        from pipeline import content_generation
        steps.append(("Content Generation", content_generation.run))

    if run_all or step_arg == "seo_optimization":
        from pipeline import seo_optimization
        steps.append(("SEO Optimization", seo_optimization.run))

    if run_all or step_arg == "publishing":
        from pipeline import publishing
        steps.append(("Publishing", publishing.run))

    if run_all or step_arg == "backlink_automation":
        from pipeline import backlink_automation
        steps.append(("Backlink Automation", backlink_automation.run))

    if run_all or step_arg == "seo_analytics":
        from pipeline import seo_analytics
        steps.append(("SEO Analytics", seo_analytics.run))

    # Execute steps
    results = {}
    for step_name, step_func in steps:
        success = run_step(step_name, step_func)
        results[step_name] = success

    # Summary
    elapsed = (datetime.utcnow() - start_time).seconds
    success_count = sum(1 for v in results.values() if v)

    console.print(f"\n{'='*60}")
    console.print(Panel.fit(
        f"[bold]Pipeline Complete[/bold]\n"
        f"Steps: {success_count}/{len(steps)} succeeded\n"
        f"Duration: {elapsed}s",
        border_style="green" if success_count == len(steps) else "yellow"
    ))

    if success_count < len(steps):
        sys.exit(1)


if __name__ == "__main__":
    main()
