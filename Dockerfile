FROM python:3.12-alpine AS base

RUN pip install --no-cache-dir poetry==1.8

WORKDIR /root/litestar_server

COPY poetry.lock pyproject.toml ./

RUN poetry install --no-cache

COPY src src

ENV PYTHONPATH=$PYTHONPATH:/root/litestar_server/src

# Can add "--reload" if developing in docker container.
CMD ["poetry", "run", "litestar", "--app-dir", "src", "run", "--host", "0.0.0.0", "--port", "8000"]
