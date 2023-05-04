# Dockerfile
FROM python:3.11-slim
# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True
COPY requirements.txt /
RUN pip3 install --no-cache-dir -r /requirements.txt
COPY .env /
COPY login_server.py .

#CMD ["gunicorn"  , "-b", "0.0.0.0:8080", "login_server:app", "--worker-class", "aiohttp.worker.GunicornWebWorker", "--log-level", "debug", "--error-logfile", "-", "--access-logfile", "-", "--capture-output"]
CMD gunicorn --bind 0.0.0.0:8080 --workers 1 --threads 2 --timeout 0 -k uvicorn.workers.UvicornWorker login_server:app
# gunicorn s:my_web_app --bind 0.0.0.0:8080 --worker-class aiohttp.GunicornWebWorker