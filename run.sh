#!/usr/bin/env bash

# For development, mount the source directory using the -v argument
# For production, use the build command

# docker build -t loudnate/naterade .
docker run -i -t \
    -p=80:5000 \
    --device=`readlink -fn /dev/serial/by-id/usb-0a21_8001-if00-port0`:/dev/serial/by-id/usb-0a21_8001-if00-port0 \
    -v=/dev/log:/dev/log \
    -v=`pwd`:/app \
    loudnate/naterade
