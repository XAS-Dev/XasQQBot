FROM python:3.11.4-slim

RUN mkdir /app
WORKDIR /app

ADD . /app/

RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
ENTRYPOINT [ "nb","run","--reload" ]