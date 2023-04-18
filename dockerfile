# Dockerfile
FROM python:alpine3.17
COPY requirements.txt /
RUN pip3 install -r /requirements.txt
COPY .env /
COPY s.py .
COPY templates /templates
COPY static /static

#EXPOSE 8080
#CMD ["gunicorn"  , "-b", "0.0.0.0:8080", "s:app", "--worker-class", "aiohttp.worker.GunicornWebWorker", "--enable-stdio-inheritance", "--log-level", "debug"]
CMD ["gunicorn"  , "-b", "0.0.0.0:8080", "s:app", "--worker-class", "aiohttp.worker.GunicornWebWorker", "--log-level", "debug", "--error-logfile", "-", "--access-logfile", "-", "--capture-output", "--reload"]

# gunicorn s:my_web_app --bind 0.0.0.0:8080 --worker-class aiohttp.GunicornWebWorker