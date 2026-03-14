FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY shared/ /app/shared/
COPY services/competitor_analysis/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/competitor_analysis/ /app/services/competitor_analysis/
RUN touch /app/services/__init__.py

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "services.competitor_analysis.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
