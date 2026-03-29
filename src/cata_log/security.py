import os
import secrets

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

http_basic_security = HTTPBasic()

depends_http_basic_security = Depends(http_basic_security)


def get_credentials() -> tuple[str, str | None]:
    """Get the credentials from the environment.

    Returns:
        Username and password.
    """
    return os.environ.get("USERNAME", "admin"), os.environ.get("PASSWORD")


def verify_credentials(
    credentials: HTTPBasicCredentials = depends_http_basic_security,
) -> None:
    """Verify credentials given by the user.

    Args:
        credentials: The user-given credentials.
    """
    username, password = get_credentials()
    if not password or not (
        secrets.compare_digest(credentials.username, username)
        and secrets.compare_digest(credentials.password, password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
