# Dockerfile
FROM python:3.11-slim
# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True
#RUN mkdir /app
#WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
ADD /static /static
CMD gunicorn --bind 0.0.0.0:8080 --workers 1 --threads 8 --timeout 0 -k uvicorn.workers.UvicornWorker login_server:app
