from _collections_abc import Iterator, dict_items, dict_keys, dict_values
from typing import ClassVar

from .base import BaseProvider


class CatalogRegistry:
    _registered_catalogs: ClassVar[dict[str, type[BaseProvider]]] = {}

    def register(self, cls: type[BaseProvider]) -> type[BaseProvider]:
        if not issubclass(cls, BaseProvider):
            raise TypeError(f"{cls} does not subclass Base")
        if cls.id in self._registered_catalogs:
            raise ValueError(f"{cls} has a non-unique id")
        self._registered_catalogs[cls.id()] = cls
        return cls

    def values(self) -> dict_values[str, type[BaseProvider]]:
        return self._registered_catalogs.values()

    def keys(self) -> dict_keys[str, type[BaseProvider]]:
        return self._registered_catalogs.keys()

    def items(self) -> dict_items[str, type[BaseProvider]]:
        return self._registered_catalogs.items()

    def __getitem__(self, key: str) -> type[BaseProvider]:
        return self._registered_catalogs[key]

    def get(self, key: str) -> type[BaseProvider] | None:
        return self._registered_catalogs.get(key)

    def __len__(self) -> int:
        return len(self._registered_catalogs.keys())

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())


catalog_registry = CatalogRegistry()
