# docker build -t tencentmusic/myapp:2020.10.01 -f install/docker/Dockerfile .

FROM tencentmusic/myapp:base

RUN apt-get update && apt-get install -y mysql-client zip

RUN curl -sL https://deb.nodesource.com/setup_14.x | bash
RUN apt-get -y install nodejs && npm install yarn -g

RUN rm /usr/bin/python && ln -s /usr/bin/python3 /usr/bin/python && rm /usr/bin/pip && ln -s /usr/bin/pip3 /usr/bin/pip

COPY install/docker/docker-add-file/__init__.py /usr/local/lib/python3.6/dist-packages/marshmallow_enum/__init__.py

COPY myapp /home/myapp/myapp
ENV PATH=/home/myapp/myapp/bin:$PATH
ENV PYTHONPATH=/home/myapp:$PYTHONPATH

USER root
COPY install/docker/entrypoint.sh /entrypoint.sh

# ENTRYPOINT ["/entrypoint.sh"]
# HEALTHCHECK CMD ["curl", "-f", "http://localhost:80/health"]






