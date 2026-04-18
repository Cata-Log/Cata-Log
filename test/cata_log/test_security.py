import pytest
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBasicCredentials
from httpx import Request, codes

from cata_log.security import verify_credentials


def test_verify_credentials__get__success(faker, fake_credentials):
    verify_credentials(
        request=Request(
            method="GET",
            url=faker.url(),
        ),
        credentials=HTTPBasicCredentials(
            username=fake_credentials[0], password=fake_credentials[1]
        ),
    )


def test_verify_credentials__post__success(faker, fake_credentials):
    verify_credentials(
        request=Request(
            method="POST",
            url=faker.url(),
        ),
        credentials=HTTPBasicCredentials(
            username=fake_credentials[0], password=fake_credentials[1]
        ),
    )


def test_verify_credentials__get__bad_auth(faker, fake_credentials):
    with pytest.raises(
        HTTPException,
    ) as exc_info:
        verify_credentials(
            request=Request(
                method="GET",
                url=faker.url(),
            ),
            credentials=HTTPBasicCredentials(
                username=faker.user_name(), password=faker.password()
            ),
        )

    assert exc_info.value.status_code == codes.UNAUTHORIZED
    assert exc_info.value.headers is not None
    assert "WWW-Authenticate" in exc_info.value.headers
    assert exc_info.value.headers["WWW-Authenticate"] == "Basic"


def test_verify_credentials__post__bad_auth(faker, fake_credentials):
    with pytest.raises(HTTPException) as exc_info:
        verify_credentials(
            request=Request(
                method="POST",
                url=faker.url(),
            ),
            credentials=HTTPBasicCredentials(
                username=faker.user_name(), password=faker.password()
            ),
        )

    assert exc_info.value.status_code == codes.UNAUTHORIZED
    assert exc_info.value.headers is not None
    assert "WWW-Authenticate" in exc_info.value.headers
    assert exc_info.value.headers["WWW-Authenticate"] == "Basic"


def test_verify_credentials__get__bad_auth__public_get(
    faker, fake_credentials, public_get
):
    verify_credentials(
        request=Request(
            method="GET",
            url=faker.url(),
        ),
        credentials=HTTPBasicCredentials(
            username=faker.user_name(), password=faker.password()
        ),
    )


def test_verify_credentials__post__bad_auth__public_get(
    faker, fake_credentials, public_get
):
    with pytest.raises(HTTPException) as exc_info:
        verify_credentials(
            request=Request(
                method="POST",
                url=faker.url(),
            ),
            credentials=HTTPBasicCredentials(
                username=faker.user_name(), password=faker.password()
            ),
        )

    assert exc_info.value.status_code == codes.UNAUTHORIZED
    assert exc_info.value.headers is not None
    assert "WWW-Authenticate" in exc_info.value.headers
    assert exc_info.value.headers["WWW-Authenticate"] == "Basic"


def test_verify_credentials__get__noauth__public_get(
    faker, fake_credentials, public_get
):
    verify_credentials(
        request=Request(
            method="GET",
            url=faker.url(),
        ),
        credentials=None,
    )


def test_verify_credentials__post__noauth__public_get(
    faker, fake_credentials, public_get
):
    with pytest.raises(HTTPException) as exc_info:
        verify_credentials(
            request=Request(
                method="POST",
                url=faker.url(),
            ),
            credentials=None,
        )

    assert exc_info.value.status_code == codes.UNAUTHORIZED
    assert exc_info.value.headers is not None
    assert "WWW-Authenticate" in exc_info.value.headers
    assert exc_info.value.headers["WWW-Authenticate"] == "Basic"


def test_verify_credentials__get__no_password(faker, fake_username):
    with pytest.raises(HTTPException) as exc_info:
        verify_credentials(
            request=Request(
                method="GET",
                url=faker.url(),
            ),
            credentials=HTTPBasicCredentials(username=fake_username, password=""),
        )

    assert exc_info.value.status_code == codes.UNAUTHORIZED
    assert exc_info.value.headers is not None
    assert "WWW-Authenticate" in exc_info.value.headers
    assert exc_info.value.headers["WWW-Authenticate"] == "Basic"


def test_verify_credentials__post__no_password(faker, fake_username):
    with pytest.raises(HTTPException) as exc_info:
        verify_credentials(
            request=Request(
                method="POST",
                url=faker.url(),
            ),
            credentials=HTTPBasicCredentials(username=fake_username, password=""),
        )
    assert exc_info.value.status_code == codes.UNAUTHORIZED
    assert exc_info.value.headers is not None
    assert "WWW-Authenticate" in exc_info.value.headers
    assert exc_info.value.headers["WWW-Authenticate"] == "Basic"


def test_verify_credentials__get__no_password__public_get(
    faker, fake_username, public_get
):
    verify_credentials(
        request=Request(
            method="GET",
            url=faker.url(),
        ),
        credentials=HTTPBasicCredentials(username=fake_username, password=""),
    )


def test_verify_credentials__post__no_password__public_get(
    faker, fake_username, public_get
):
    with pytest.raises(HTTPException) as exc_info:
        verify_credentials(
            request=Request(
                method="POST",
                url=faker.url(),
            ),
            credentials=HTTPBasicCredentials(username=fake_username, password=""),
        )

    assert exc_info.value.status_code == codes.UNAUTHORIZED
    assert exc_info.value.headers is not None
    assert "WWW-Authenticate" in exc_info.value.headers
    assert exc_info.value.headers["WWW-Authenticate"] == "Basic"
