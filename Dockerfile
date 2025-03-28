FROM python:3.8-slim AS builder

WORKDIR /app
COPY ./ ./
RUN pip install poetry

RUN poetry config virtualenvs.create false  && poetry install --no-interaction --no-root

EXPOSE 8080

CMD ["python", "app/src/app/app.py"]