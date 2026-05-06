# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Copyright © 2026 David Aderbauer & The Cata-Log Contributors

ARG PYTHON_VERSION=3.14
ARG ALPINE_VERSION=3.23

ARG STORAGE_PATH=/mnt/storage/
ARG LOG_PATH=/var/log/cata-log/
ARG DATABASE_PATH=/mnt/db
ARG PLUGIN_PATH=/mnt/plugins

##    stage 1    ##
## convert pyproject.toml to requirements file for python dependencies ##
## no cleanup required ##

FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION} AS uv-prestage

WORKDIR /

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv && \
    uv export --format requirements.txt --frozen --no-dev > /requirements.txt


##   stage 2   ##
## compile final image  ##
## cleanup mandatory ##
## order operations by increasing frequency of change ##

FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION} AS cata-log

# labels
LABEL org.opencontainers.image.authors="David Aderbauer & The Cata-Log Contributors"
LABEL org.opencontainers.image.documentation="https://cata-log.readthedocs.io"
LABEL org.opencontainers.image.source="https://gitlab.com/cata-log/cata-log"
LABEL org.opencontainers.image.url="https://gitlab.com/cata-log/cata-log"
LABEL org.opencontainers.image.licenses="AGPL-3.0-or-later"
LABEL org.opencontainers.image.description="The central hub for grocery shopping catalogs."
LABEL org.opencontainers.image.title="Cata-Log Server"

ARG SRC_PATH=/opt/
ARG STORAGE_PATH
ARG DATABASE_PATH
ARG LOG_PATH
ARG PLUGIN_PATH

WORKDIR ${SRC_PATH}

# environment setup
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# install python dependencies
COPY --from=uv-prestage /requirements.txt ./

RUN pip install --no-cache-dir --requirement requirements.txt && \
    rm -f requirements.txt && \
    rm -rf /tmp/*

# install cata_log
COPY pyproject.toml src/ ./

RUN pip install --no-cache-dir . && \
    rm -rf /tmp/* && \
    rm -rf ./*

# set default settings for dockerized usage
ENV HOST="0.0.0.0" \
    PORT=2424 \
    DATABASE_PATH=${DATABASE_PATH} \
    LOG_PATH=${LOG_PATH} \
    PLUGIN_PATH=${PLUGIN_PATH} \
    STORAGE_PATH=${STORAGE_PATH}

WORKDIR /

# must match port used by cata-log
EXPOSE 2424

VOLUME ${STORAGE_PATH} ${LOG_PATH} ${DATABASE_PATH} ${PLUGIN_PATH}

ENTRYPOINT [ "python3", "-m" , "cata_log"]

HEALTHCHECK --interval=60s --timeout=30s --start-period=3s --retries=3 CMD [ "wget", "--quiet", "http://0.0.0.0:8000/health", "--output-document" , "/dev/null"]
