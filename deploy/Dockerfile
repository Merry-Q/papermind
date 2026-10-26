FROM node:22-slim AS node-runtime

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PAPERMIND_DATA_DIR=/var/lib/papermind

WORKDIR /app
COPY --from=node-runtime /usr/local/bin/node /usr/local/bin/node
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && groupadd -g 10002 papermind \
    && useradd -u 10002 -g 10002 -M papermind
COPY backend /app/backend
COPY agents/skills /app/agents/skills
COPY frontend/dist /app/frontend/dist
COPY frontend/node_modules/katex/dist/katex.mjs /app/frontend/node_modules/katex/dist/katex.mjs
COPY frontend/reading-v2-runtime.js /app/frontend/reading-v2-runtime.js
COPY scripts/render-reading-math.mjs /app/scripts/render-reading-math.mjs

USER papermind
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=3).close()"
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*"]
