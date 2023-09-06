FROM python:3.11-alpine
WORKDIR /app

RUN apk update && \
    apk add --virtual .tmp build-base python3-dev \
    libpq postgresql-dev gcc jpeg-dev zlib-dev libffi-dev && \
    apk del .tmp

COPY requirements.in .
RUN pip install pip-tools && pip-compile && pip install -r requirements.txt && \
    apk add postgresql-dev jpeg-dev 
COPY . .

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

CMD [
    "gunicorn", "--reload", "--workers=2", "--worker-tmp-dir", "/dev/shm",
    "--bind=0.0.0.0:80", "--chdir", "/app/social", "social.wsgi"
    ]
