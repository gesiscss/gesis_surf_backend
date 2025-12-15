FROM python:3.10-alpine
LABEL maintainer="Mario Ramirez marm1984@gmail.com"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./scripts /scripts
COPY ./app /app
WORKDIR /app
EXPOSE 8000

ARG DEV=false
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql && \
    apk add --update --no-cache --virtual .tmp-build-dev \
    build-base postgresql-dev musl-dev linux-headers && \
    apk add --update --no-cache graphviz graphviz-dev && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ] ; then /py/bin/pip install -r /tmp/requirements.dev.txt ; fi && \
    rm -rf /tmp && \
    apk del .tmp-build-dev && \
    adduser \
    --disabled-password \
    --no-create-home \
    django-user && \
    mkdir -p /vol/media && \
    mkdir -p /vol/static && \
    mkdir -p /opt/web_tracker/security_scripts && \
    chown -R django-user:django-user /vol && \
    chmod -R 755 /vol && \
    chmod -R +x /scripts && \
    chown -R django-user:django-user /opt/web_tracker/security_scripts


COPY ./security_scripts /opt/web_tracker/security_scripts
RUN chmod -R 755 /opt/web_tracker/security_scripts/manage_patterns.py

ENV PATH="/scripts:/py/bin:$PATH"

USER django-user

CMD ["run.sh"]
