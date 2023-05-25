FROM python:3.10

ENV PYTHONUNBUFFERED=true
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.4.2
ENV PATH="$PATH:$POETRY_HOME/bin"

ADD ./backend/pyproject.toml .
ADD ./backend/src/fantasy_footballer .
ADD ./backend/README.md .

RUN python -m pip install "poetry==${POETRY_VERSION}"
RUN poetry install --no-interaction --no-ansi

EXPOSE 8000

ENTRYPOINT ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
