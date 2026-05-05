# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Copyright © 2026 David Aderbauer & The Cata-Log Contributors

ARG PYTHON_VERSION=3.14
ARG ALPINE_VERSION=3.23

ARG STORAGE_PATH=/mnt/storage/  # must match STORAGE_PATH in constants
ARG LOG_PATH=/var/log/cata-log/  # must match LOG_DIRECTORY_PATH in constants
ARG DATABASE_PATH=/mnt/db  # must match DATABASE_PATH in constants
ARG PLUGIN_PATH=/mnt/plugins  # must match PLUGIN_PATH in constants

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
    PYTHONPATH=${SRC_PATH} \
    PYTHONUNBUFFERED=1

VOLUME ${STORAGE_PATH} ${LOG_PATH} ${DATABASE_PATH} ${PLUGIN_PATH}

ENTRYPOINT [ "fastapi", "run" , "cata_log/main.py"]

# install python dependencies
COPY --from=uv-prestage /requirements.txt ./

ARG BUILD_PYTHON_APK_DEPENDENCIES

RUN pip install --no-cache-dir --requirement requirements.txt && \
    rm -rf /tmp/* && \
    rm -f requirements.txt

COPY pyproject.toml src/ ./

# must match port used by fastapi
EXPOSE 8000
