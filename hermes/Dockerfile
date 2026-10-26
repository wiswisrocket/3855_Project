FROM python:3.14-slim

RUN pip install requests redis pyyaml

ENV PYTHONUNBUFFERED=1

COPY . /app
WORKDIR /app

CMD ["python", "hermes.py"]