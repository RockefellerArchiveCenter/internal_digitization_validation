FROM python:3.12-alpine AS base

ENV PYTHONUNBUFFERED=1

WORKDIR /code
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src src

FROM base AS test
COPY test_requirements.txt .coveragerc ./
RUN pip install -r test_requirements.txt
COPY tests tests

FROM base AS build
CMD [ "python", "src/process_packages.py" ]