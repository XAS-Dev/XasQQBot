FROM python:3.12.2-slim

WORKDIR /app
ADD . /app/

RUN pip install nb-cli -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install . -i https://pypi.tuna.tsinghua.edu.cn/simple

ENTRYPOINT [ "nb","run","--reload" ]