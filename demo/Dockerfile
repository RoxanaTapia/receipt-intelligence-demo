# Build from the repo root so vendor/demo-kit is in the context:
#   docker build -f demo/Dockerfile .
FROM python:3.12-slim

WORKDIR /app

COPY demo/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY demo/app ./app
COPY demo/seed ./seed
COPY demo/samples ./samples
COPY vendor/demo-kit ./vendor/demo-kit

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
