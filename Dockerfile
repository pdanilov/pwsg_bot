FROM python:3.9.5 AS production
WORKDIR /code
COPY Pipfile* ./
RUN pip install pipenv
RUN pipenv install --system --deploy
COPY . ./
ENTRYPOINT ["python", "-m", "app"]

FROM production AS development
RUN pipenv install --system --deploy --dev
