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
    def __init__(self, page_number: int, start_number: int = 0) -> None:
        self._number = page_number - start_number
        self._offset = start_number

    def __repr__(self) -> str:
        return f"Page {self._number}"

    def __hash__(self) -> int:
        return hash(self._number)

    def __int__(self) -> int:
        return self._number + self._offset

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PageNumber):
            return other._number == self._number and other._offset == self._offset
        if isinstance(other, DoublePageNumber):
            return self.as_double_page_number() == other
        if isinstance(other, int):
            return int(self) == other
        return False

    def next(self) -> PageNumber:
        return PageNumber(int(self) + 1, self._offset)

    def prev(self) -> PageNumber | None:
        if self._number == 0:
            return None
        return PageNumber(int(self) - 1, self._offset)

    def as_double_page_number(self) -> DoublePageNumber:
        return DoublePageNumber(
            (self._number - 1) // 2 + 1,
            (self._number + 1) % 2 if self._number != 0 else 0,
            self._offset,
        )

    @property
    def normalized(self) -> int:
        return self._number


class DoublePageNumber:
    def __init__(
        self, double_page_number: int, double_page_index: int, start_number: int = 0
    ) -> None:
        self._number = double_page_number
        if self._number == 0:
            self._index = 0
        else:
            self._index = double_page_index % 2
        self._offset = start_number

    def __repr__(self) -> str:
        return f"Double page {self._number}, side {self._index}"

    def __hash__(self) -> int:
        return hash((self._number, self._index))

    def __int__(self) -> int:
        return self._number

    def __eq__(self, other: object) -> bool:
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
        if self._number == 0:
            return DoublePageNumber(1, 0, self._offset)
        return DoublePageNumber(
            self._number + self._index,
            (self._index + 1) % 2,
            self._offset,
        )

    def prev(self) -> DoublePageNumber | None:
        if self._number == 0:
            return None
        return DoublePageNumber(
            int(self._number) - (self._index - 1) % 2,
            (self._index - 1) % 2,
            self._offset,
        )

    def as_page_number(self) -> PageNumber:
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
