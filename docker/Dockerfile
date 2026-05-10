# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Copyright © 2026 David Aderbauer & The Cata-Log Contributors

ARG PYTHON_VERSION=3.14
ARG ALPINE_VERSION=3.23

ARG DATA_PATH=/mnt/
ARG LOGS_PATH=/var/log/cata-log/


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

# environment setup
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ARG DATA_PATH
ARG LOGS_PATH

# set default settings for dockerized usage
ENV CATA_LOG_DATA_PATH=${DATA_PATH} \
    CATA_LOG_STORAGE_PATH=${DATA_PATH}/storage \
    CATA_LOG_DATABASE_PATH=${DATA_PATH}/db \
    CATA_LOG_PLUGIN_PATH=${DATA_PATH}/plugins \
    CATA_LOG_LOGS_PATH=${LOGS_PATH}

VOLUME ${DATA_PATH}/storage ${DATA_PATH}/db ${DATA_PATH}/plugins ${LOGS_PATH}

EXPOSE 8000

# installation
WORKDIR /opt/

# install python dependencies
COPY --from=uv-prestage /requirements.txt ./

RUN pip install --no-cache-dir --requirement requirements.txt && \
    rm -rf /root/.cache && \
    rm -f requirements.txt && \
    rm -rf /tmp/*

# install cata_log
COPY pyproject.toml src/ ./

RUN pip install --no-cache-dir . && \
    rm -rf /root/.cache && \
    rm -rf /tmp/* && \
    rm -rf ./*

WORKDIR /

ENTRYPOINT [ "python3", "-m" , "cata_log", "--host", "0.0.0.0", "--port", "8000"]

HEALTHCHECK --interval=60s --timeout=30s --start-period=3s --retries=3 CMD [ "wget", "--quiet", "http://0.0.0.0:8000/health", "--output-document" , "/dev/null"]
