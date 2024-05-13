FROM python:3.12.2-slim

WORKDIR /app
ADD . /app/

ARG MIRROR=https://pypi.org/simple

RUN pip install nb-cli -i ${MIRROR}
RUN pip install . -i ${MIRROR}

ENTRYPOINT [ "nb","run","--reload" ]