FROM mcr.microsoft.com/playwright/python:v1.63.0-noble

RUN python -m pip install --no-cache-dir 'playwright==1.63.0' \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin collector \
    && mkdir /data \
    && chown 10001:10001 /data

WORKDIR /app
COPY --chown=10001:10001 collector.py /app/collector.py
USER 10001:10001
ENV HOME=/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "/app/collector.py"]
