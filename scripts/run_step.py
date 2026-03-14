#!/usr/bin/env python3
"""Run a single pipeline step by name."""
import sys
import logging
import importlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)

STEP_MAP = {
    "keyword_discovery":   "pipeline.keyword_discovery",
    "competitor_analysis": "pipeline.competitor_analysis",
    "content_generation":  "pipeline.content_generation",
    "seo_optimization":    "pipeline.seo_optimization",
    "publishing":          "pipeline.publishing",
    "render_articles":     "scripts.render_articles",
    "backlink_automation": "pipeline.backlink_automation",
    "seo_analytics":       "pipeline.seo_analytics",
    "dashboard":           "scripts.generate_dashboard",
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_step.py <step_name>")
        print(f"Steps: {', '.join(STEP_MAP.keys())}")
        sys.exit(1)

    step = sys.argv[1]

    if step not in STEP_MAP:
        print(f"Unknown step: '{step}'")
        print(f"Available: {', '.join(STEP_MAP.keys())}")
        sys.exit(1)

    module = importlib.import_module(STEP_MAP[step])
    # All modules expose run(); generate_dashboard exposes generate() as well
    runner = getattr(module, 'run', None) or getattr(module, 'generate', None)
    if not runner:
        print(f"Module {STEP_MAP[step]} has no run() or generate() function")
        sys.exit(1)

    runner()


if __name__ == "__main__":
    main()
