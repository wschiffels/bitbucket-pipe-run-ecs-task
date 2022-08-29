FROM python:alpine3.15
LABEL maintainer=wolfgang@rubarb.app

RUN apk add --no-cache --upgrade --virtual .build-dev build-base libffi-dev \
    && pip3 install boto3 bitbucket_pipes_toolkit \
    && apk del .build-dev \
    && rm -rf /root/.cache/

COPY run_task.py /
ENTRYPOINT ["/usr/local/bin/python3", "/run_task.py"]
