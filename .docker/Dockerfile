# https://fastapi.tiangolo.com/deployment/docker/
#
FROM python:3.9

WORKDIR /app
COPY ./.docker/requirements.txt /app/
COPY ./app/files /app/files
COPY ./app/main /app/main
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
CMD ["uvicorn", "main.main:app", "--host", "0.0.0.0", "--port", "443"]
