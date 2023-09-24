FROM python:3.11.4-slim

WORKDIR /app
ADD . /app/

RUN pip install . -i https://pypi.tuna.tsinghua.edu.cn/simple

ENTRYPOINT [ "nb","run","--reload" ]