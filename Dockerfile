FROM python:3.8.10
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt && pip install gunicorn
COPY . /code/
CMD gunicorn centhroid.wsgi --bind 0.0.0.0:80 --timeout 0 --workers 1 --threads 8