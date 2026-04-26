# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Copyright © 2026 David Aderbauer & The Cata-Log Contributors

ARG PYTHON_VERSION=3.14
ARG ALPINE_VERSION=3.23
ARG S6_OVERLAY_VERSION=3.2.1.0

ARG RUNTIME_APK_DEPENDENCIES="rabbitmq-server"

ARG BUILD_PYTHON_APK_DEPENDENCIES=""

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
## download and unpack s6-overlay ##
## no cleanup required ##

FROM alpine:${ALPINE_VERSION} AS s6-overlay-prestage

ARG S6_OVERLAY_VERSION

WORKDIR /tmp

# install s6-overlay
ARG TARGETARCH
ARG TARGETVARIANT

ARG BUILD_S6_APK_DEPENDENCIES="curl xz"

RUN apk add --no-cache ${BUILD_S6_APK_DEPENDENCIES} && \
    S6_ARCH="" && \
    if [ "${TARGETARCH}""${TARGETVARIANT}" = "amd64" ]; then S6_ARCH="x86_64"; \
    elif [ "${TARGETARCH}""${TARGETVARIANT}" = "arm64" ]; then S6_ARCH="aarch64"; fi && \
    if [ -z "${S6_ARCH}" ]; then { echo "Error: Not able to determine target platform"; exit 1; }; fi && \
    curl --fail --silent --no-progress-meter --show-error --location --remote-name-all --parallel --parallel-max 4 \
    "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz" \
    "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz.sha256" \
    "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${S6_ARCH}.tar.xz" \
    "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${S6_ARCH}.tar.xz.sha256" && \
    sha256sum -c ./*.sha256 && \
    mkdir -p /s6-overlay && \
    tar --directory /s6-overlay -Jxpf "s6-overlay-noarch.tar.xz" && \
    tar --directory /s6-overlay -Jxpf "s6-overlay-${S6_ARCH}.tar.xz"

##   stage 3   ##
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
ARG S6_OVERLAY_PATH=/etc/s6-overlay/
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

# setup s6-overlay
COPY --from=s6-overlay-prestage /s6-overlay/ /

COPY --chmod=550 ./docker/s6-overlay/ ${S6_OVERLAY_PATH}

ENTRYPOINT [ "/init" ]

# install apk runtime dependencies
ARG RUNTIME_APK_DEPENDENCIES

RUN apk update && \
    apk add --no-cache ${RUNTIME_APK_DEPENDENCIES} && \
    rm -rf /var/cache/apk/* && \
    rm -rf /tmp/*

# install python dependencies
COPY --from=uv-prestage /requirements.txt ./

ARG BUILD_PYTHON_APK_DEPENDENCIES

RUN apk add --no-cache ${BUILD_PYTHON_APK_DEPENDENCIES} && \
    pip install --no-cache-dir --requirement requirements.txt && \
    apk del ${BUILD_PYTHON_APK_DEPENDENCIES} && \
    rm -rf /var/cache/apk/* && \
    rm -rf /tmp/* && \
    rm -f requirements.txt


COPY pyproject.toml src/ ./

# must match port used by fastapi
EXPOSE 8000
