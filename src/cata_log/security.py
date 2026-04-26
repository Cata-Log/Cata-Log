import os
import secrets

from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from cata_log.settings import Settings

http_basic_security = HTTPBasic(auto_error=False)

depends_http_basic_security = Depends(http_basic_security)


def get_credentials() -> tuple[str, str | None]:
    """Get the credentials from the environment.

    Returns:
        Username and password.
    """
    return os.environ.get("USERNAME", "admin"), os.environ.get("PASSWORD")


def verify_credentials(
    request: Request,
    credentials: HTTPBasicCredentials | None = depends_http_basic_security,
) -> None:
    """Verify credentials given by the user.

    Args:
        request: The request that needs to be authenticated.
        credentials: The user-given credentials.
    """
    if Settings.PUBLIC_GET.value and request.method == "GET":
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
