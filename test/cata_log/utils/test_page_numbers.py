import pytest

from cata_log.utils import page_numbers


@pytest.mark.parametrize(
    ("page_number", "start_number"),
    [
        (10, 22),
        (3, 4),
        (-1, 0),
    ],
)
def test_PageNumber__invalid(page_number, start_number):
    with pytest.raises(ValueError):  # noqa: PT011 # nothing reasonable to match
        page_numbers.PageNumber(page_number, start_number)


def test_PageNumber__properties(faker):
    fake_start_number = faker.random.randint(0, 100)
    fake_number = fake_start_number + faker.random.randint(0, 100)

    page_number = page_numbers.PageNumber(fake_number, fake_start_number)

    assert page_number.normalized == fake_number - fake_start_number
    assert int(page_number) == fake_number
    assert repr(page_number)
    assert str(page_number)


@pytest.mark.parametrize(
    ("page_number", "equal_object"),
    [
        (page_numbers.PageNumber(0, 0), 0),
        (page_numbers.PageNumber(1, 0), 1),
        (page_numbers.PageNumber(2, 0), page_numbers.PageNumber(2, 0)),
        (page_numbers.PageNumber(3, 0), page_numbers.PageNumber(3, 0)),
        (page_numbers.PageNumber(4, 0), page_numbers.DoublePageNumber(2, 1, 0)),
        (page_numbers.PageNumber(1, 1), page_numbers.DoublePageNumber(0, 0, 1)),
        (page_numbers.PageNumber(3, 2), page_numbers.DoublePageNumber(1, 0, 2)),
        (page_numbers.PageNumber(2, 1), page_numbers.PageNumber(2, 1)),
        (page_numbers.PageNumber(4, 2), 4.0),
        (page_numbers.PageNumber(1, 1), 1.0),
    ],
)
def test_PageNumber___eq___equal(page_number, equal_object):
    assert page_number == equal_object


@pytest.mark.parametrize(
    ("page_number", "unequal_object"),
    [
        (page_numbers.PageNumber(0, 0), 4),
        (page_numbers.PageNumber(1, 0), 7),
        (page_numbers.PageNumber(2, 0), page_numbers.PageNumber(2, 1)),
        (page_numbers.PageNumber(3, 0), page_numbers.PageNumber(2, 0)),
        (page_numbers.PageNumber(4, 0), page_numbers.DoublePageNumber(3, 1, 0)),
        (page_numbers.PageNumber(1, 1), page_numbers.DoublePageNumber(1, 0, 2)),
        (page_numbers.PageNumber(3, 2), page_numbers.DoublePageNumber(1, 1, 2)),
        (page_numbers.PageNumber(2, 1), [2, 1]),
        (page_numbers.PageNumber(2, 1), (2, 1)),
        (page_numbers.PageNumber(2, 1), 4.6),
        (page_numbers.PageNumber(4, 1), 0.3),
    ],
)
def test_PageNumber___eq___unequal(page_number, unequal_object):
    assert page_number != unequal_object


@pytest.mark.parametrize(
    ("page_number", "smaller_object"),
    [
        (page_numbers.PageNumber(1, 0), 0),
        (page_numbers.PageNumber(3, 2), 0),
        (page_numbers.PageNumber(2, 0), page_numbers.PageNumber(1, 0)),
        (page_numbers.PageNumber(3, 0), page_numbers.PageNumber(2, 1)),
        (page_numbers.PageNumber(4, 0), page_numbers.DoublePageNumber(1, 1, 0)),
        (page_numbers.PageNumber(2, 1), page_numbers.DoublePageNumber(0, 0, 1)),
        (page_numbers.PageNumber(4, 2), page_numbers.DoublePageNumber(1, 0, 2)),
        (page_numbers.PageNumber(2, 1), page_numbers.PageNumber(1, 1)),
        (page_numbers.PageNumber(3, 2), 1.0),
        (page_numbers.PageNumber(2, 1), 0.3),
    ],
)
def test_PageNumber___gt___greater(page_number, smaller_object):
    assert page_number > smaller_object


@pytest.mark.parametrize(
    ("page_number", "greater_object"),
    [
        (page_numbers.PageNumber(0, 0), 1),
        (page_numbers.PageNumber(1, 0), 2),
        (page_numbers.PageNumber(2, 0), page_numbers.PageNumber(4, 1)),
        (page_numbers.PageNumber(3, 0), page_numbers.PageNumber(4, 0)),
        (page_numbers.PageNumber(4, 0), page_numbers.DoublePageNumber(3, 1, 0)),
        (page_numbers.PageNumber(1, 1), page_numbers.DoublePageNumber(1, 1, 2)),
        (page_numbers.PageNumber(3, 2), page_numbers.DoublePageNumber(2, 0, 2)),
        (page_numbers.PageNumber(2, 1), 3.0),
        (page_numbers.PageNumber(4, 2), 5.0),
    ],
)
def test_PageNumber___gt___smaller(page_number, greater_object):
    assert page_number < greater_object


@pytest.mark.parametrize(
    ("page_number", "incomparable_object"),
    [
        (page_numbers.PageNumber(0, 0), ["list"]),
        (page_numbers.PageNumber(1, 0), {1: "dict"}),
    ],
)
def test_PageNumber___gt___incomparable(page_number, incomparable_object):
    with pytest.raises(TypeError):
        page_number < incomparable_object  # noqa: B015 # not pointless, triggers error


@pytest.mark.parametrize(
    ("summand_1", "summand_2", "expected_sum"),
    [
        (page_numbers.PageNumber(3, 0), 0, page_numbers.PageNumber(3, 0)),
        (page_numbers.PageNumber(0, 0), 1, page_numbers.PageNumber(1, 0)),
        (page_numbers.PageNumber(1, 1), 2, page_numbers.PageNumber(3, 1)),
    ],
)
def test_PageNumber___add__(summand_1, summand_2, expected_sum):
    assert summand_1 + summand_2 == expected_sum


@pytest.mark.parametrize(
    ("summand_1", "summand_2"),
    [
        (page_numbers.PageNumber(3, 0), "str"),
        ([1, "list"], page_numbers.PageNumber(0, 0)),
        (page_numbers.PageNumber(1, 1), {1: "dict"}),
    ],
)
def test_PageNumber___add___incompatible(summand_1, summand_2):
    with pytest.raises(TypeError):
        summand_1 + summand_2


@pytest.mark.parametrize(
    ("minuend", "subtrahend", "expected_difference"),
    [
        (page_numbers.PageNumber(1, 0), 1, page_numbers.PageNumber(0, 0)),
        (page_numbers.PageNumber(4, 2), 2, page_numbers.PageNumber(2, 2)),
        (page_numbers.PageNumber(3, 2), 0, page_numbers.PageNumber(3, 2)),
    ],
)
def test_PageNumber___sub__(minuend, subtrahend, expected_difference):
    assert minuend - subtrahend == expected_difference


@pytest.mark.parametrize(
    ("minuend", "subtrahend"),
    [
        (page_numbers.PageNumber(3, 0), "str"),
        ([1, "list"], page_numbers.PageNumber(0, 0)),
        (page_numbers.PageNumber(1, 1), {1: "dict"}),
    ],
)
def test_PageNumber___sub___incompatible(minuend, subtrahend):
    with pytest.raises(TypeError):
        minuend - subtrahend


def test_PageNumber__hashable():
    assert {page_numbers.PageNumber(0, 0)}


def test_DoublePageNumber__properties(faker):
    fake_start_number = faker.random.randint(0, 100)
    fake_number = fake_start_number + faker.random.randint(1, 100)
    fake_index = faker.random.randint(0, 1)

    double_page_number = page_numbers.DoublePageNumber(
        fake_number, fake_index, fake_start_number
    )

    assert double_page_number.side == fake_index
    assert double_page_number.number == fake_number
    assert int(double_page_number) == fake_number
    assert repr(double_page_number)
    assert str(double_page_number)


@pytest.mark.parametrize(
    ("double_page_number", "equal_object"),
    [
        (page_numbers.DoublePageNumber(0, 0, 0), 0),
        (page_numbers.DoublePageNumber(1, 0, 0), 1),
        (page_numbers.DoublePageNumber(2, 1, 0), page_numbers.PageNumber(4, 0)),
        (page_numbers.DoublePageNumber(3, 0, 0), page_numbers.PageNumber(5, 0)),
        (
            page_numbers.DoublePageNumber(2, 1, 0),
            page_numbers.DoublePageNumber(2, 1, 0),
        ),
        (
            page_numbers.DoublePageNumber(0, 0, 1),
            page_numbers.DoublePageNumber(0, 0, 1),
        ),
        (
            page_numbers.DoublePageNumber(1, 0, 2),
            page_numbers.DoublePageNumber(1, 0, 2),
        ),
        (page_numbers.DoublePageNumber(3, 1, 1), page_numbers.PageNumber(7, 1)),
        (page_numbers.DoublePageNumber(2, 0, 1), 4.0),
        (page_numbers.DoublePageNumber(3, 1, 0), 6.0),
    ],
)
def test_DoublePageNumber___eq___equal(double_page_number, equal_object):
    assert double_page_number == equal_object


@pytest.mark.parametrize(
    ("double_page_number", "unequal_object"),
    [
        (page_numbers.DoublePageNumber(0, 0, 0), 4),
        (page_numbers.DoublePageNumber(1, 0, 0), 7),
        (page_numbers.DoublePageNumber(2, 1, 0), page_numbers.PageNumber(2, 1)),
        (page_numbers.DoublePageNumber(3, 0, 0), page_numbers.PageNumber(2, 0)),
        (
            page_numbers.DoublePageNumber(4, 1, 0),
            page_numbers.DoublePageNumber(3, 1, 0),
        ),
        (
            page_numbers.DoublePageNumber(1, 0, 1),
            page_numbers.DoublePageNumber(0, 0, 2),
        ),
        (
            page_numbers.DoublePageNumber(3, 0, 2),
            page_numbers.DoublePageNumber(1, 1, 2),
        ),
        (page_numbers.DoublePageNumber(2, 1, 1), [2, 1]),
        (page_numbers.DoublePageNumber(2, 1, 1), (2, 1)),
        (page_numbers.DoublePageNumber(1, 0, 0), 7.3),
        (page_numbers.DoublePageNumber(2, 1, 0), 2.6),
    ],
)
def test_DoublePageNumber___eq___unequal(double_page_number, unequal_object):
    assert double_page_number != unequal_object


@pytest.mark.parametrize(
    ("double_page_number", "smaller_object"),
    [
        (page_numbers.DoublePageNumber(1, 0, 0), 0),
        (page_numbers.DoublePageNumber(2, 1, 0), 1),
        (page_numbers.DoublePageNumber(2, 1, 0), page_numbers.PageNumber(3, 0)),
        (page_numbers.DoublePageNumber(3, 0, 0), page_numbers.PageNumber(4, 0)),
        (
            page_numbers.DoublePageNumber(3, 0, 0),
            page_numbers.DoublePageNumber(2, 1, 0),
        ),
        (
            page_numbers.DoublePageNumber(1, 1, 1),
            page_numbers.DoublePageNumber(1, 0, 1),
        ),
        (
            page_numbers.DoublePageNumber(5, 0, 2),
            page_numbers.DoublePageNumber(1, 0, 2),
        ),
        (page_numbers.DoublePageNumber(1, 1, 0), 1.4),
        (page_numbers.DoublePageNumber(3, 1, 0), 2.3),
    ],
)
def test_DoublePageNumber___gt___greater(double_page_number, smaller_object):
    assert double_page_number > smaller_object


@pytest.mark.parametrize(
    ("double_page_number", "greater_object"),
    [
        (page_numbers.DoublePageNumber(0, 0, 0), 1),
        (page_numbers.DoublePageNumber(1, 0, 0), 2),
        (page_numbers.DoublePageNumber(2, 1, 0), page_numbers.PageNumber(6, 1)),
        (page_numbers.DoublePageNumber(3, 0, 0), page_numbers.PageNumber(7, 0)),
        (
            page_numbers.DoublePageNumber(2, 1, 0),
            page_numbers.DoublePageNumber(3, 1, 0),
        ),
        (
            page_numbers.DoublePageNumber(4, 0, 1),
            page_numbers.DoublePageNumber(4, 1, 1),
        ),
        (
            page_numbers.DoublePageNumber(3, 0, 2),
            page_numbers.DoublePageNumber(5, 1, 2),
        ),
        (page_numbers.DoublePageNumber(1, 1, 0), 3.6),
        (page_numbers.DoublePageNumber(3, 1, 0), 8.2),
    ],
)
def test_DoublePageNumber___gt___smaller(double_page_number, greater_object):
    assert double_page_number < greater_object


@pytest.mark.parametrize(
    ("double_page_number", "incomparable_object"),
    [
        (page_numbers.DoublePageNumber(0, 0, 0), ["list"]),
        (page_numbers.DoublePageNumber(1, 0, 0), {1: "dict"}),
    ],
)
def test_DoublePageNumber___gt___incomparable(double_page_number, incomparable_object):
    with pytest.raises(TypeError):
        double_page_number < incomparable_object  # noqa: B015 # not pointless, triggers error


@pytest.mark.parametrize(
    ("summand_1", "summand_2", "expected_sum"),
    [
        (
            page_numbers.DoublePageNumber(4, 2, 1),
            0,
            page_numbers.DoublePageNumber(4, 2, 1),
        ),
        (
            page_numbers.DoublePageNumber(0, 0, 0),
            1,
            page_numbers.DoublePageNumber(1, 0, 0),
        ),
        (
            page_numbers.DoublePageNumber(1, 0, 0),
            2,
            page_numbers.DoublePageNumber(2, 0, 0),
        ),
    ],
)
def test_DoublePageNumber___add__(summand_1, summand_2, expected_sum):
    assert summand_1 + summand_2 == expected_sum


@pytest.mark.parametrize(
    ("minuend", "subtrahend", "expected_difference"),
    [
        (
            page_numbers.DoublePageNumber(4, 2, 1),
            0,
            page_numbers.DoublePageNumber(4, 2, 1),
        ),
        (
            page_numbers.DoublePageNumber(2, 0, 0),
            1,
            page_numbers.DoublePageNumber(1, 1, 0),
        ),
        (
            page_numbers.DoublePageNumber(2, 1, 0),
            2,
            page_numbers.DoublePageNumber(1, 1, 0),
        ),
    ],
)
def test_DoublePageNumber___sub__(minuend, subtrahend, expected_difference):
    assert minuend - subtrahend == expected_difference


def test_DoublePageNumber___hashable():
    assert {page_numbers.DoublePageNumber(0, 0, 0)}


@pytest.mark.parametrize(
    ("page_number", "expected_next_page_number"),
    [
        (page_numbers.PageNumber(0, 0), page_numbers.PageNumber(1, 0)),
        (page_numbers.PageNumber(1, 0), page_numbers.PageNumber(2, 0)),
        (page_numbers.PageNumber(2, 0), page_numbers.PageNumber(3, 0)),
        (page_numbers.PageNumber(3, 0), page_numbers.PageNumber(4, 0)),
        (page_numbers.PageNumber(4, 0), page_numbers.PageNumber(5, 0)),
        (page_numbers.PageNumber(1, 1), page_numbers.PageNumber(2, 1)),
        (page_numbers.PageNumber(2, 1), page_numbers.PageNumber(3, 1)),
        (page_numbers.PageNumber(3, 2), page_numbers.PageNumber(4, 2)),
        (page_numbers.PageNumber(5, 3), page_numbers.PageNumber(6, 3)),
    ],
)
def test_PageNumber_next(page_number, expected_next_page_number):
    result = page_number.next()

    assert result == expected_next_page_number


@pytest.mark.parametrize(
    ("page_number", "expected_prev_page_number"),
    [
        (page_numbers.PageNumber(0, 0), None),
        (page_numbers.PageNumber(1, 0), page_numbers.PageNumber(0, 0)),
        (page_numbers.PageNumber(2, 0), page_numbers.PageNumber(1, 0)),
        (page_numbers.PageNumber(3, 0), page_numbers.PageNumber(2, 0)),
        (page_numbers.PageNumber(4, 0), page_numbers.PageNumber(3, 0)),
        (page_numbers.PageNumber(1, 1), None),
        (page_numbers.PageNumber(2, 1), page_numbers.PageNumber(1, 1)),
        (page_numbers.PageNumber(3, 2), page_numbers.PageNumber(2, 2)),
        (page_numbers.PageNumber(5, 3), page_numbers.PageNumber(4, 3)),
    ],
)
def test_PageNumber_prev(page_number, expected_prev_page_number):
    result = page_number.prev()

    assert result == expected_prev_page_number


@pytest.mark.parametrize(
    ("double_page_number", "expected_next_double_page_number"),
    [
        (
            page_numbers.DoublePageNumber(0, 0, 0),
            page_numbers.DoublePageNumber(1, 0, 0),
        ),
        (
            page_numbers.DoublePageNumber(1, 0, 0),
            page_numbers.DoublePageNumber(1, 1, 0),
        ),
        (
            page_numbers.DoublePageNumber(1, 1, 0),
            page_numbers.DoublePageNumber(2, 0, 0),
        ),
        (
            page_numbers.DoublePageNumber(2, 0, 0),
            page_numbers.DoublePageNumber(2, 1, 0),
        ),
        (
            page_numbers.DoublePageNumber(2, 1, 0),
            page_numbers.DoublePageNumber(3, 0, 0),
        ),
        (
            page_numbers.DoublePageNumber(3, 0, 0),
            page_numbers.DoublePageNumber(3, 1, 0),
        ),
        (
            page_numbers.DoublePageNumber(0, 1, 0),
            page_numbers.DoublePageNumber(1, 0, 0),
        ),
        (
            page_numbers.DoublePageNumber(1, 0, 1),
            page_numbers.DoublePageNumber(1, 1, 1),
        ),
        (
            page_numbers.DoublePageNumber(2, 0, 1),
            page_numbers.DoublePageNumber(2, 1, 1),
        ),
        (
            page_numbers.DoublePageNumber(2, 1, 1),
            page_numbers.DoublePageNumber(3, 0, 1),
        ),
        (
            page_numbers.DoublePageNumber(3, 0, 3),
            page_numbers.DoublePageNumber(3, 1, 3),
        ),
        (
            page_numbers.DoublePageNumber(3, 1, 3),
            page_numbers.DoublePageNumber(4, 0, 3),
        ),
    ],
)
def test_DoublePageNumber_next(double_page_number, expected_next_double_page_number):
    result = double_page_number.next()

    assert result == expected_next_double_page_number


@pytest.mark.parametrize(
    ("double_page_number", "expected_prev_double_page_number"),
    [
        (page_numbers.DoublePageNumber(0, 0, 0), None),
        (
            page_numbers.DoublePageNumber(1, 0, 0),
            page_numbers.DoublePageNumber(0, 0, 0),
        ),
        (
            page_numbers.DoublePageNumber(1, 1, 0),
            page_numbers.DoublePageNumber(1, 0, 0),
        ),
        (
            page_numbers.DoublePageNumber(2, 0, 0),
            page_numbers.DoublePageNumber(1, 1, 0),
        ),
        (
            page_numbers.DoublePageNumber(2, 1, 0),
            page_numbers.DoublePageNumber(2, 0, 0),
        ),
        (
            page_numbers.DoublePageNumber(3, 0, 0),
            page_numbers.DoublePageNumber(2, 1, 0),
        ),
        (page_numbers.DoublePageNumber(0, 1, 0), None),
        (
            page_numbers.DoublePageNumber(1, 0, 1),
            page_numbers.DoublePageNumber(0, 0, 1),
        ),
        (
            page_numbers.DoublePageNumber(2, 0, 1),
            page_numbers.DoublePageNumber(1, 1, 1),
        ),
        (
            page_numbers.DoublePageNumber(2, 1, 1),
            page_numbers.DoublePageNumber(2, 0, 1),
        ),
        (
            page_numbers.DoublePageNumber(3, 0, 3),
            page_numbers.DoublePageNumber(2, 1, 3),
        ),
        (
            page_numbers.DoublePageNumber(3, 1, 3),
            page_numbers.DoublePageNumber(3, 0, 3),
        ),
    ],
)
def test_DoublePageNumber_prev(double_page_number, expected_prev_double_page_number):
    result = double_page_number.prev()

    assert result == expected_prev_double_page_number


@pytest.mark.parametrize(
    ("double_page_number", "expected_page_number"),
    [
        (page_numbers.DoublePageNumber(0, 0, 0), page_numbers.PageNumber(0, 0)),
        (page_numbers.DoublePageNumber(1, 0, 0), page_numbers.PageNumber(1, 0)),
        (page_numbers.DoublePageNumber(1, 1, 0), page_numbers.PageNumber(2, 0)),
        (page_numbers.DoublePageNumber(2, 0, 0), page_numbers.PageNumber(3, 0)),
        (page_numbers.DoublePageNumber(2, 1, 0), page_numbers.PageNumber(4, 0)),
        (page_numbers.DoublePageNumber(3, 0, 0), page_numbers.PageNumber(5, 0)),
        (page_numbers.DoublePageNumber(3, 1, 0), page_numbers.PageNumber(6, 0)),
        (page_numbers.DoublePageNumber(0, 1, 0), page_numbers.PageNumber(0, 0)),
        (page_numbers.DoublePageNumber(1, 0, 1), page_numbers.PageNumber(2, 1)),
        (page_numbers.DoublePageNumber(2, 0, 1), page_numbers.PageNumber(4, 1)),
        (page_numbers.DoublePageNumber(2, 1, 1), page_numbers.PageNumber(5, 1)),
        (page_numbers.DoublePageNumber(3, 0, 1), page_numbers.PageNumber(6, 1)),
        (page_numbers.DoublePageNumber(3, 1, 1), page_numbers.PageNumber(7, 1)),
        (page_numbers.DoublePageNumber(3, 0, 3), page_numbers.PageNumber(8, 3)),
        (page_numbers.DoublePageNumber(3, 1, 3), page_numbers.PageNumber(9, 3)),
    ],
)
def test_DoublePageNumber_as_page_number(double_page_number, expected_page_number):
    result = double_page_number.as_page_number()

    assert result == expected_page_number


@pytest.mark.parametrize(
    ("page_number", "expected_double_page_number"),
    [
        (page_numbers.PageNumber(0, 0), page_numbers.DoublePageNumber(0, 0, 0)),
        (page_numbers.PageNumber(1, 0), page_numbers.DoublePageNumber(1, 0, 0)),
        (page_numbers.PageNumber(2, 0), page_numbers.DoublePageNumber(1, 1, 0)),
        (page_numbers.PageNumber(3, 0), page_numbers.DoublePageNumber(2, 0, 0)),
        (page_numbers.PageNumber(4, 0), page_numbers.DoublePageNumber(2, 1, 0)),
        (page_numbers.PageNumber(5, 0), page_numbers.DoublePageNumber(3, 0, 0)),
        (page_numbers.PageNumber(6, 0), page_numbers.DoublePageNumber(3, 1, 0)),
        (page_numbers.PageNumber(0, 0), page_numbers.DoublePageNumber(0, 1, 0)),
        (page_numbers.PageNumber(1, 1), page_numbers.DoublePageNumber(0, 0, 1)),
        (page_numbers.PageNumber(2, 1), page_numbers.DoublePageNumber(1, 0, 1)),
        (page_numbers.PageNumber(3, 1), page_numbers.DoublePageNumber(1, 1, 1)),
        (page_numbers.PageNumber(4, 1), page_numbers.DoublePageNumber(2, 0, 1)),
        (page_numbers.PageNumber(5, 1), page_numbers.DoublePageNumber(2, 1, 1)),
        (page_numbers.PageNumber(6, 5), page_numbers.DoublePageNumber(1, 0, 5)),
    ],
)
def test_PageNumber_as_double_page_number(page_number, expected_double_page_number):
    result = page_number.as_double_page_number()

    assert result == expected_double_page_number


@pytest.mark.parametrize("start_number", [0, 1, 4])
def test_page_numbering(start_number):
    for expected_page_number, page_number in enumerate(
        page_numbers.page_numbering(start_number), start_number
    ):
        assert int(page_number) == expected_page_number
        assert page_number.normalized == expected_page_number - start_number
        if expected_page_number == 10:
            break
