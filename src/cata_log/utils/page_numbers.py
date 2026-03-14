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


class PageNumber:
    """Pagenumber logic class."""

    def __init__(self, page_number: int, start_number: int = 0) -> None:
        """Constructor for the pagenumber.

        Args:
            page_number: The pagenumber.
            start_number: The number of the first page.
        """
        self._number = page_number - start_number
        self._offset = start_number

    def __repr__(self) -> str:
        """Representation of the pagenumber.

        Returns:
            The string representation.
        """
        return f"Page {self._number}"

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

    def __eq__(self, other: object) -> bool:
        """Comparison of the pagenumber, double-pagenumber and int.

        Returns:
            Whether the objects are equal.
        """
        if isinstance(other, PageNumber):
            return other._number == self._number and other._offset == self._offset
        if isinstance(other, DoublePageNumber):
            return self.as_double_page_number() == other
        if isinstance(other, int):
            return int(self) == other
        return False

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


class DoublePageNumber:
    """Pagenumber logic class."""

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

    def __repr__(self) -> str:
        """Representation of the pagenumber.

        Returns:
            The string representation.
        """
        return f"Double page {self._number}, side {self._index}"

    def __hash__(self) -> int:
        """Hash of the pagenumber.

        Returns:
            The hash value.
        """
        return hash((self._number, self._index))

    def __int__(self) -> int:
        """The double-pagenumber.

        Returns:
            The non-normalized original pagenumber.
        """
        return self._number

    def __eq__(self, other: object) -> bool:
        """Comparison of the double-pagenumber, double-pagenumber and int.

        Returns:
            Whether the objects are equal.
        """
        if isinstance(other, DoublePageNumber):
            return (
                other._number == self._number
                and other._index == self._index
                and other._offset == self._offset
            )
        if isinstance(other, PageNumber):
            return self.as_page_number() == other
        if isinstance(other, int):
            return int(self) == other
        return False

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
            0
            if self._number == 0
            else self._number * 2 - 1 + self._index + self._offset,
            self._offset,
        )


def page_number_2_double_page_number(
    page_number: int, first_page_number: int = 0
) -> int:
    return (page_number - first_page_number + 1) // 2


def page_number_2_double_page_index(
    page_number: int, first_page_number: int = 0
) -> int:
    return (
        (page_number - first_page_number + 1) % 2
        if page_number != first_page_number
        else 0
    )
