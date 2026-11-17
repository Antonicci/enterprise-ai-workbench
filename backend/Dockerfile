FROM python:3.12-slim
WORKDIR /app
COPY backend/pyproject.toml backend/pyproject.toml
COPY backend/requirements.lock backend/requirements.lock
COPY backend/workbench backend/workbench
RUN pip install --no-cache-dir -r backend/requirements.lock && pip install --no-deps ./backend && useradd --create-home workbench
USER workbench
CMD ["uvicorn", "workbench.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
