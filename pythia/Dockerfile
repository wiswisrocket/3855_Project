FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install connexion[uvicorn] connexion[swagger-ui] redis pyyaml

COPY . /app
WORKDIR /app

EXPOSE 8011
CMD ["uvicorn", "pythia:app", "--host", "0.0.0.0", "--port", "8011"]
