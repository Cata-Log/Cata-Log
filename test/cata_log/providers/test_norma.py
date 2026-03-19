import httpx
import pytest
from freezegun import freeze_time

from cata_log.providers import Norma
from cata_log.utils.dates import get_calendar_week_number


def test_Norma_get_page__success(faker, httpx_mock):
    fake_datetime = faker.date_time()
    fake_page_number = faker.random.randint(0, 10)
    fake_bytes = faker.text().encode()
    httpx_mock.add_response(
        url="https://www.norma-online.de/de/angebote/online-prospekt/{year}-{week_number:02}_FG/files/page/{page_number}.jpg".format(
            year=fake_datetime.year,
            week_number=get_calendar_week_number(
                fake_datetime, Norma.region.week_counting_startpoint
            ),
            page_number=fake_page_number,
        ),
        method="GET",
        content=fake_bytes,
        match_extensions={"follow_redirects": True},
    )

    with freeze_time(fake_datetime):
        result = Norma().get_page(fake_page_number)

    assert result == fake_bytes


def test_Norma_get_page__404(faker, httpx_mock):
    fake_datetime = faker.date_time()
    fake_page_number = faker.random.randint(0, 10)
    fake_bytes = faker.text().encode()
    httpx_mock.add_response(
        url="https://www.norma-online.de/de/angebote/online-prospekt/{year}-{week_number:02}_FG/files/page/{page_number}.jpg".format(
            year=fake_datetime.year,
            week_number=get_calendar_week_number(
                fake_datetime, Norma.region.week_counting_startpoint
            ),
            page_number=fake_page_number,
        ),
        method="GET",
        match_extensions={"follow_redirects": True},
        status_code=404,
    )

    with freeze_time(fake_datetime):
        with pytest.raises(httpx.HTTPStatusError):
            Norma().get_page(fake_page_number)


def test_Norma_get_page__401(faker, httpx_mock):
    fake_datetime = faker.date_time()
    fake_page_number = faker.random.randint(0, 10)
    fake_bytes = faker.text().encode()
    httpx_mock.add_response(
        url="https://www.norma-online.de/de/angebote/online-prospekt/{year}-{week_number:02}_FG/files/page/{page_number}.jpg".format(
            year=fake_datetime.year,
            week_number=get_calendar_week_number(
                fake_datetime, Norma.region.week_counting_startpoint
            ),
            page_number=fake_page_number,
        ),
        method="GET",
        match_extensions={"follow_redirects": True},
        status_code=404,
    )

    with freeze_time(fake_datetime):
        with pytest.raises(httpx.HTTPStatusError):
            Norma().get_page(fake_page_number)
