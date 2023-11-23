FROM python:3.11

RUN curl -sSL https://install.python-poetry.org | python3.11 -
ENV PATH /root/.local/bin:$PATH

WORKDIR /code

COPY pyproject.toml poetry.lock /code/
RUN poetry install --without dev --no-root --no-cache

COPY . /code

CMD ["make", "run"]