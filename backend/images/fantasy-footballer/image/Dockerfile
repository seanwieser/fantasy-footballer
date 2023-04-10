FROM python:3.9.10-slim-buster
ENV PYTHONUNBUFFERED=True
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.1.14
ENV PATH="$PATH:$POETRY_HOME/bin"

RUN apt-get update && apt-get install --no-install-recommends -y curl\
    && curl -sSL https://install.python-poetry.org | python \
    && rm -rf /var/lib/apt/lists/*

ADD ./src .
ADD pyproject.toml .
ADD README.md .
RUN poetry install

ADD ./images/commons-table-creator/image/extra_docker_pip_requirements.txt .
ADD ./images/fantasy-footballer/image/run.py .
RUN python -m pip install -r extra_docker_pip_requirements.txt
ENTRYPOINT ["python", "run.py"]