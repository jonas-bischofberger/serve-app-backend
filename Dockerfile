# https://fastapi.tiangolo.com/deployment/docker/
# 
FROM python:3.9

WORKDIR /serve-app-backend
COPY . /serve-app-backend
RUN pip install --no-cache-dir --upgrade -r /serve-app-backend/requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "443"]
