FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install connexion[uvicorn] connexion[swagger-ui] requests

COPY . /app
WORKDIR /app

EXPOSE 8080
CMD ["uvicorn", "receiver:app", "--host", "0.0.0.0", "--port", "8080"]
