# docker build -t tencentmusic/myapp:myapp-upgrade -f upgrade/Dockerfile .

FROM python:3.6

RUN pip install flask

COPY upgrade /upgrade

WORKDIR /upgrade

CMD ['python','server.py']






