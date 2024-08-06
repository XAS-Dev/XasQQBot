FROM python:3.11.9-alpine

WORKDIR /app
ADD . /app/

ARG MIRROR=https://pypi.org/simple

RUN pip install pdm nb-cli -i ${MIRROR}
RUN pdm config pypi.url ${MIRROR}
RUN pdm install

ENTRYPOINT [ "nb", "run", "--reload" ]