FROM python:3.13.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --upgrade pip==25.1.1 setuptools==80.9.0 wheel==0.45.1 \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -e .

COPY . .

CMD ["python", "-m", "llm_sqa.cli", "doctor"]
