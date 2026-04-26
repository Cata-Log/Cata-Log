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


from collections.abc import Generator
from functools import total_ordering
from typing import override


@total_ordering
class PageNumber:
    """Pagenumber logic class."""

    @override
    def __init__(self, page_number: int, start_number: int = 0) -> None:
        """Constructor for the pagenumber.

        Args:
            page_number: The pagenumber.
            start_number: The number of the first page.
        """
        self._number = page_number - start_number
        self._offset = start_number

    @override
    def __repr__(self) -> str:
        """Representation of the pagenumber.

        Returns:
            The string representation.
        """
        return f"Page {self._number}"

    def __add__(self, other: object) -> PageNumber:
        """Add another object to this instance.
        Implemented for int, DoublePageNumber and PageNumber.

        Returns:
            The sum of this instance and the other object.

        Raises:
            TypeError: If the other object is of incompatible type.
        """
        if isinstance(other, int):
            return PageNumber(self._number + other + self._offset, self._offset)
        raise TypeError("Cannot add this object to this pagenumber.")

    def __sub__(self, other: object) -> PageNumber:
        """Subtract another object from this instance.
        Implemented for int, DoublePageNumber and PageNumber.

        Returns:
            The difference of this instance and the other object.

        Raises:
            TypeError: If the other object is of incompatible type.
        """
        if isinstance(other, int):
            return PageNumber(self._number - other + self._offset, self._offset)
        raise TypeError("Cannot subtract this object from this pagenumber.")

    @override
    def __hash__(self) -> int:
        """Hash of the pagenumber.

        Returns:
            The hash value.
        """
        return hash(self._number)

    def __int__(self) -> int:
        """The pagenumber as one integer.

        Returns:
            The non-normalized original pagenumber.
        """
        return self._number + self._offset

    @override
    def __str__(self) -> str:
        """Convert the pagenumber as a string.

        Returns:
            The pagenumber as a numeric string.
        """
        return str(int(self))

    @override
    def __eq__(self, other: object) -> bool:
        """Comparison of the pagenumber, double-pagenumber and int.

        Returns:
            Whether the objects are equal.
        """
        if isinstance(other, PageNumber):
            return other._number == self._number
        if isinstance(other, DoublePageNumber):
            return self == other.as_page_number()
        if isinstance(other, (int, float)):
            return int(self) == other
        return NotImplemented

    def __gt__(self, other: object) -> bool:
        """Comparison of the pagenumber, double-pagenumber and int.

        Returns:
            Whether this object is greater than the other.
        """
        if isinstance(other, PageNumber):
            return self._number > other._number
        if isinstance(other, DoublePageNumber):
            return self > other.as_page_number()
        if isinstance(other, (int, float)):
            return int(self) > other
        return NotImplemented

    def next(self) -> PageNumber:
        """Get the next pagenumber.

        Returns:
            The next pagenumber class.
        """
        return PageNumber(int(self) + 1, self._offset)

    def prev(self) -> PageNumber | None:
        """Get the previous pagenumber.

        Returns:
            The previous pagenumber class. None if this is the first page.
        """
        if self._number == 0:
            return None
        return PageNumber(int(self) - 1, self._offset)

    def as_double_page_number(self) -> DoublePageNumber:
        """Get the pagenumber as a double-pagenumber.

        Returns:
            The double-pagenumber class equivalent to this pagenumber.
        """
        return DoublePageNumber(
            (self._number - 1) // 2 + 1,
            (self._number + 1) % 2 if self._number != 0 else 0,
            self._offset,
        )

    @property
    def normalized(self) -> int:
        """The normalized pagenumber."""
        return self._number


@total_ordering
class DoublePageNumber:
    """Pagenumber logic class."""

    @override
    def __init__(
        self, double_page_number: int, double_page_index: int, start_number: int = 0
    ) -> None:
        """Constructor for the pagenumber.

        Args:
            double_page_number: The pagenumber.
            double_page_index: The index of the page within the double page.
            start_number: The number of the first page.
        """
        self._number = double_page_number
        if self._number == 0:
            self._index = 0
        else:
            self._index = double_page_index % 2
        self._offset = start_number

    @override
    def __repr__(self) -> str:
        """Representation of the pagenumber.

        Returns:
            The string representation.
        """
        return f"Double page {self._number}, side {self._index}"

    @override
    def __hash__(self) -> int:
        """Hash of the pagenumber.

        Returns:
            The hash value.
        """
        return hash((self._number, self._index))

    def __add__(self, other: object) -> DoublePageNumber:
        """Add another object to this instance.
        Implemented for int, DoublePageNumber and PageNumber.

        Returns:
            The sum of this instance and the other object.

        Raises:
            TypeError: If the other object is of incompatible type.
        """
        return (self.as_page_number() + other).as_double_page_number()

    def __sub__(self, other: object) -> DoublePageNumber:
        """Subtract another object from this instance.
        Implemented for int, DoublePageNumber and PageNumber.

        Returns:
            The difference between this instance and the other object.

        Raises:
            TypeError: If the other object is of incompatible type.
        """
        return (self.as_page_number() - other).as_double_page_number()

    def __int__(self) -> int:
        """The double-pagenumber.

        Returns:
            The non-normalized original pagenumber.
        """
        return self._number

    @override
    def __eq__(self, other: object) -> bool:
        """Comparison of the double-pagenumber, pagenumber and int.

        Returns:
            Whether the objects are equal.
        """
        return self.as_page_number() == other

    def __gt__(self, other: object) -> bool:
        """Comparison of the double-pagenumber, pagenumber and int.

        Returns:
            Whether this object is greater than the other.
        """
        return self.as_page_number() > other

    def next(self) -> DoublePageNumber:
        """Get the next double-pagenumber.

        Returns:
            The next double-pagenumber class.
        """
        if self._number == 0:
            return DoublePageNumber(1, 0, self._offset)
        return DoublePageNumber(
            self._number + self._index,
            (self._index + 1) % 2,
            self._offset,
        )

    def prev(self) -> DoublePageNumber | None:
        """Get the previous double-pagenumber.

        Returns:
            The previous double-pagenumber class. None if this is the first double-page.
        """
        if self._number == 0:
            return None
        return DoublePageNumber(
            int(self._number) - (self._index - 1) % 2,
            (self._index - 1) % 2,
            self._offset,
        )

    def as_page_number(self) -> PageNumber:
        """Get double-pagenumber as a pagenumber.

        Returns:
            The pagenumber class equivalent to this double-pagenumber.
        """
        return PageNumber(
            self._offset
            if self._number == 0
            else self._number * 2 - 1 + self._index + self._offset,
            self._offset,
        )

    @property
    def number(self) -> int:
        """Number of the double page.

        Returns:
            The number of this double page.
        """
        return self._number

    @property
    def side(self) -> int:
        """Index of the double page side.

        Returns:
            The index of this page.
        """
        return self._index


def page_numbering(start_number: int = 0) -> Generator[PageNumber]:
    """Generator for a page numbering.

    Args:
        start_number: The first page number.

    Yields:
        The consecutive page numbers starting with the first page number.
    """
    page_number = PageNumber(start_number, start_number=start_number)
    while True:
        yield page_number
        page_number = page_number.next()
