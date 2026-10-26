FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install connexion[uvicorn] connexion[swagger-ui] sqlalchemy mysqlclient pyyaml

COPY . /app
WORKDIR /app

EXPOSE 8090
CMD ["uvicorn", "storage:app", "--host", "0.0.0.0", "--port", "8090"]
