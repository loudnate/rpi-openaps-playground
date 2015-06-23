FROM loudnate/rpi-openaps
MAINTAINER Nathan Racklyeft <loudnate@gmail.com>

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python-flask \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

RUN easy_install cachetools openapscontrib.mmhistorytools

EXPOSE 80

COPY . /app

WORKDIR /app

RUN git init && \
    git config user.name "Nathan Racklyeft" && \
    git config user.email loudnate@gmail.com

CMD python app.py
