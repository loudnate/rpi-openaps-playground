FROM loudnate/rpi-openaps
MAINTAINER Nathan Racklyeft <loudnate@gmail.com>

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python-flask \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

RUN easy_install cachetools

ADD . /app

EXPOSE 80

WORKDIR /app

CMD python app.py
