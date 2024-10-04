FROM python:3.12.5-slim-bullseye

ENV PYTHONUNBUFFERED=true
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.8.3
ENV PATH="$PATH:$POETRY_HOME/bin"

RUN pip install "poetry==${POETRY_VERSION}"
ADD ./pyproject.toml .
ADD ./poetry.lock .

RUN poetry install --no-interaction --no-ansi

ADD ./images/fantasy-footballer/data ./data
ADD ./images/fantasy-footballer/media ./media
ADD ./src/fantasy_footballer .
ADD ./README.md .

ENTRYPOINT ["poetry", "run", "python3", "main.py"]
