.PHONY: install run-pipeline run-step test lint clean setup-secrets help

help:
	@echo "Kubegraf SEO Automation - Available Commands:"
	@echo "  make install          - Install Python dependencies"
	@echo "  make run-pipeline     - Run the full SEO pipeline"
	@echo "  make run-keyword      - Run keyword discovery only"
	@echo "  make run-competitors  - Run competitor analysis only"
	@echo "  make run-content      - Run content generation only"
	@echo "  make run-optimize     - Run SEO optimization only"
	@echo "  make run-publish      - Run publishing only"
	@echo "  make run-analytics    - Run SEO analytics only"
	@echo "  make dashboard        - Generate static dashboard"
	@echo "  make setup-secrets    - Instructions to set GitHub secrets"
	@echo "  make lint             - Run code linter"
	@echo "  make clean            - Clean generated files"

install:
	pip install -r requirements.txt

run-pipeline:
	PYTHONPATH=. python scripts/run_pipeline.py

run-keyword:
	PYTHONPATH=. python scripts/run_step.py keyword_discovery

run-competitors:
	PYTHONPATH=. python scripts/run_step.py competitor_analysis

run-content:
	PYTHONPATH=. python scripts/run_step.py content_generation

run-optimize:
	PYTHONPATH=. python scripts/run_step.py seo_optimization

run-publish:
	PYTHONPATH=. python scripts/run_step.py publishing

run-analytics:
	PYTHONPATH=. python scripts/run_step.py seo_analytics

dashboard:
	PYTHONPATH=. python scripts/run_step.py dashboard

lint:
	python -m py_compile pipeline/*.py shared/*.py shared/models.py scripts/*.py
	@echo "✅ All files pass syntax check"

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

setup-secrets:
	@echo "Required GitHub Secrets (Settings -> Secrets -> Actions):"
	@echo ""
	@echo "  GEMINI_API_KEY  - Your Google Gemini API key"
	@echo "                    Get from: https://aistudio.google.com/app/apikey"
	@echo ""
	@echo "  GITHUB_TOKEN is automatically provided by GitHub Actions."
	@echo ""
	@echo "Optional:"
	@echo "  GOOGLE_SEARCH_CONSOLE_KEY - For real rank tracking"
	@echo ""
	@echo "To trigger manually:"
	@echo "  gh workflow run seo-pipeline.yml"
	@echo "  gh workflow run seo-pipeline.yml -f step=content_generation -f articles_per_run=5"

test:
	PYTHONPATH=. python -c "\
from shared.models import Article, Keyword, Competitor, SEOReport; \
from shared import storage; \
from pipeline.seo_optimization import calculate_seo_score; \
print('✅ Models import OK'); \
print('✅ Storage import OK'); \
print('✅ SEO scoring import OK'); \
a = Article(title='Test Article', slug='test', meta_description='Test', content='# Test\n\nContent here', keywords=['test'], category='test', article_type='test'); \
score = calculate_seo_score(a); \
print(f'✅ SEO score calculation OK: {score}'); \
print('All tests passed!') \
"
