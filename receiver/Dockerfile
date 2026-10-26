FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install connexion[flask] connexion[uvicorn] connexion[swagger-ui] requests

COPY . /app
WORKDIR . /app

EXPOSE 12345
CMD ["uvicorn", "receiver:app", "--host", "0.0.0.0", "--port", "12345"]
