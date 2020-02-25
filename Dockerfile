FROM python:3.7

WORKDIR /app

RUN pip install pipenv
COPY Pipfile* ./
RUN pipenv lock --requirements > requirements.txt
RUN pip install -r requirements.txt

COPY . .

ENV FLASK_APP web.py

CMD [ "flask", "run", "--host=0.0.0.0" ]
