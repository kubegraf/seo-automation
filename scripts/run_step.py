#!/usr/bin/env python3
"""Run a single pipeline step by name."""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_step.py <step_name>")
        print("Steps: keyword_discovery, competitor_analysis, content_generation,")
        print("       seo_optimization, publishing, backlink_automation, seo_analytics")
        sys.exit(1)

    step = sys.argv[1]

    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    step_map = {
        "keyword_discovery": "pipeline.keyword_discovery",
        "competitor_analysis": "pipeline.competitor_analysis",
        "content_generation": "pipeline.content_generation",
        "seo_optimization": "pipeline.seo_optimization",
        "publishing": "pipeline.publishing",
        "backlink_automation": "pipeline.backlink_automation",
        "seo_analytics": "pipeline.seo_analytics",
        "dashboard": "scripts.generate_dashboard",
    }

    if step not in step_map:
        print(f"Unknown step: {step}")
        print(f"Available: {', '.join(step_map.keys())}")
        sys.exit(1)

    import importlib
    module = importlib.import_module(step_map[step])

    if step == "dashboard":
        module.generate()
    else:
        module.run()


if __name__ == "__main__":
    main()
