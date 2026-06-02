import pytest
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBasicCredentials
from httpx import Request, codes

from cata_log_hub import security


def test_verify_credentials__get__success(faker, fake_credentials):
    security.verify_credentials(
        request=Request(
            method="GET",
            url=faker.uri_path(),
        ),
        credentials=HTTPBasicCredentials(
            username=fake_credentials[0], password=fake_credentials[1]
        ),
    )


def test_verify_credentials__post__success(faker, fake_credentials):
    security.verify_credentials(
        request=Request(
            method="POST",
            url=faker.uri_path(),
        ),
        credentials=HTTPBasicCredentials(
            username=fake_credentials[0], password=fake_credentials[1]
        ),
    )


def test_verify_credentials__get__bad_auth(faker, fake_credentials):
    with pytest.raises(
        HTTPException,
    ) as exc_info:
        security.verify_credentials(
            request=Request(
                method="GET",
                url=faker.uri_path(),
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
        security.verify_credentials(
            request=Request(
                method="POST",
                url=faker.uri_path(),
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
    security.verify_credentials(
        request=Request(
            method="GET",
            url=faker.uri_path(),
        ),
        credentials=HTTPBasicCredentials(
            username=faker.user_name(), password=faker.password()
        ),
    )


def test_verify_credentials__post__bad_auth__public_get(
    faker, fake_credentials, public_get
):
    with pytest.raises(HTTPException) as exc_info:
        security.verify_credentials(
            request=Request(
                method="POST",
                url=faker.uri_path(),
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
    security.verify_credentials(
        request=Request(
            method="GET",
            url=faker.uri_path(),
        ),
        credentials=None,
    )


def test_verify_credentials__post__noauth__public_get(
    faker, fake_credentials, public_get
):
    with pytest.raises(HTTPException) as exc_info:
        security.verify_credentials(
            request=Request(
                method="POST",
                url=faker.uri_path(),
            ),
            credentials=None,
        )

    assert exc_info.value.status_code == codes.UNAUTHORIZED
    assert exc_info.value.headers is not None
    assert "WWW-Authenticate" in exc_info.value.headers
    assert exc_info.value.headers["WWW-Authenticate"] == "Basic"


def test_verify_credentials__get__no_password(faker, fake_username):
    with pytest.raises(HTTPException) as exc_info:
        security.verify_credentials(
            request=Request(
                method="GET",
                url=faker.uri_path(),
            ),
            credentials=HTTPBasicCredentials(username=fake_username, password=""),
        )

    assert exc_info.value.status_code == codes.UNAUTHORIZED
    assert exc_info.value.headers is not None
    assert "WWW-Authenticate" in exc_info.value.headers
    assert exc_info.value.headers["WWW-Authenticate"] == "Basic"


def test_verify_credentials__post__no_password(faker, fake_username):
    with pytest.raises(HTTPException) as exc_info:
        security.verify_credentials(
            request=Request(
                method="POST",
                url=faker.uri_path(),
            ),
            credentials=HTTPBasicCredentials(username=fake_username, password=""),
        )
    assert exc_info.value.status_code == codes.UNAUTHORIZED
    assert exc_info.value.headers is not None
    assert "WWW-Authenticate" in exc_info.value.headers
    assert exc_info.value.headers["WWW-Authenticate"] == "Basic"


def test_verify_credentials__get__noauth__unprotected(faker, fake_credentials):
    url_path = faker.uri_path()
    security.UNPROTECTED_PATHS = (url_path, *security.UNPROTECTED_PATHS)

    security.verify_credentials(
        request=Request(
            method="GET",
            url=url_path,
        ),
        credentials=None,
    )


def test_verify_credentials__post__noauth__unprotected(faker, fake_credentials):
    url_path = faker.uri_path()
    security.UNPROTECTED_PATHS = (url_path, *security.UNPROTECTED_PATHS)

    security.verify_credentials(
        request=Request(
            method="POST",
            url=url_path,
        ),
        credentials=None,
    )


def test_verify_credentials__get__no_password__public_get(
    faker, fake_username, public_get
):
    security.verify_credentials(
        request=Request(
            method="GET",
            url=faker.uri_path(),
        ),
        credentials=HTTPBasicCredentials(username=fake_username, password=""),
    )


def test_verify_credentials__post__no_password__public_get(
    faker, fake_username, public_get
):
    with pytest.raises(HTTPException) as exc_info:
        security.verify_credentials(
            request=Request(
                method="POST",
                url=faker.uri_path(),
            ),
            credentials=HTTPBasicCredentials(username=fake_username, password=""),
        )

    assert exc_info.value.status_code == codes.UNAUTHORIZED
    assert exc_info.value.headers is not None
    assert "WWW-Authenticate" in exc_info.value.headers
    assert exc_info.value.headers["WWW-Authenticate"] == "Basic"
