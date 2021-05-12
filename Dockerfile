FROM python:3.9.5

WORKDIR /code
COPY Pipfile* /code
RUN pip install pipenv && \
    pipenv install --system --deploy
ADD . .
