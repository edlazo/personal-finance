# syntax=docker/dockerfile:1

# --- build: instala las dependencias en un venv aislado ------------------------
FROM python:3.14.8-slim AS build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

# --- runtime: solo el venv y el código, con usuario sin privilegios ------------
FROM python:3.14.8-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --system --uid 10001 --no-create-home app

WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY pyproject.toml ./
COPY migrations ./migrations
COPY src ./src

USER app
EXPOSE 8000

CMD ["fastapi", "run", "src/app/main.py", "--host", "0.0.0.0", "--port", "8000"]
