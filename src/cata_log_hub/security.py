# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Cata-Log - the central hub for grocery store catalogs
# Copyright (C) 2026 David Aderbauer & The Cata-Log Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import secrets

from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from cata_log_hub.settings import get_settings

http_basic_security = HTTPBasic(auto_error=False)

depends_http_basic_security = Depends(http_basic_security)

UNPROTECTED_PATHS = ("/health",)


def get_credentials() -> tuple[str, str | None]:
    """Get the credentials from the environment.

    Returns:
        Username and password.
    """
    settings = get_settings()
    return settings.username, settings.password


def verify_credentials(
    request: Request,
    credentials: HTTPBasicCredentials | None = depends_http_basic_security,
) -> None:
    """Verify credentials given by the user.

    Args:
        request: The request that needs to be authenticated.
        credentials: The user-given credentials.
    """
    if get_settings().public_get and request.method == "GET":
        return
    if request.url.path in UNPROTECTED_PATHS:
        return
    username, password = get_credentials()
    if (
        (credentials is None)
        or not password
        or not (
            secrets.compare_digest(credentials.username, username)
            and secrets.compare_digest(credentials.password, password)
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
