FROM python:3.12.5-slim-bullseye

ENV PYTHONUNBUFFERED=true
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.8.3
ENV PATH="$PATH:$POETRY_HOME/bin"

RUN pip install "poetry==${POETRY_VERSION}"
COPY ./pyproject.toml .
COPY ./poetry.lock .

RUN poetry install --no-interaction --no-ansi

COPY ./src/fantasy_footballer .
COPY ./dbt/fantasy_footballer ./dbt/fantasy_footballer/
COPY ./README.md .

EXPOSE 8080

ENTRYPOINT ["poetry", "run", "python3", "main.py"]
