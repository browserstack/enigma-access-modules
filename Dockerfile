############################################################
# Dockerfile to run a Django-based web application
# Based on an AMI
############################################################
# Set the base image to use to Ubuntu
FROM python:3.11-slim-buster AS base

RUN DEBIAN_FRONTEND=noninteractive \
  apt-get update -y \
  && apt-get install --no-install-recommends -y \
  openssh-client curl procps git vim gcc linux-libc-dev libc6-dev build-essential \
  && apt-get clean \
  && apt-get autoremove -y

# Set env variables used in this Dockerfile (add a unique prefix, such as DEV)
RUN apt update && apt install -y netcat dnsutils libmariadbclient-dev git

RUN mkdir -p /ebs/logs && touch /ebs/logs/engima.log && chmod 777 /ebs/logs/engima.log

ARG APPUID=1001
RUN useradd -rm -d /home/app -s /bin/bash -g root -G sudo -u "$APPUID" app
WORKDIR /srv/code/dev
RUN git clone https://github.com/browserstack/enigma.git .
RUN mkdir -p Access/access_modules
COPY config.json.sample config.json
RUN cp requirements.txt /tmp/
RUN mkdir -p logs
RUN mkdir -p db
RUN chown -R app /srv/code/dev /ebs
USER app

COPY requirements.txt /tmp/access-module-requirements.txt
RUN pip install -r /tmp/requirements.txt --no-cache-dir --ignore-installed
RUN pip install -r /tmp/access-module-requirements.txt --no-cache-dir --ignore-installed
COPY --chown=app:root aws_access ./Access/access_modules/aws_access
COPY --chown=app:root confluence ./Access/access_modules/confluence
COPY --chown=app:root gcp ./Access/access_modules/gcp
COPY --chown=app:root github_access ./Access/access_modules/github_access
COPY --chown=app:root opsgenie_access ./Access/access_modules/opsgenie_access
COPY --chown=app:root slack_access ./Access/access_modules/slack_access
COPY --chown=app:root ssh ./Access/access_modules/ssh
COPY --chown=app:root zoom_access ./Access/access_modules/zoom_access

# Starts Docker Container and keeps it running for Debugging
FROM base as test
ENTRYPOINT ["tail", "-f", "/dev/null"]
