from _collections_abc import Iterator, dict_items, dict_keys, dict_values

from .base import Base


class CatalogRegistry:
    _registered_catalogs: dict[str, type[Base]] = {}

    def register(self, cls: type[Base]) -> type[Base]:
        self._registered_catalogs[cls.id] = cls
        return cls

    def values(self) -> dict_values[str, type[Base]]:
        return self._registered_catalogs.values()

    def keys(self) -> dict_keys[str, type[Base]]:
        return self._registered_catalogs.keys()

    def items(self) -> dict_items[str, type[Base]]:
        return self._registered_catalogs.items()

    def __getitem__(self, key: str) -> type[Base]:
        return self._registered_catalogs[key]

    def get(self, key: str) -> type[Base] | None:
        return self._registered_catalogs.get(key)

    def __len__(self) -> int:
        return len(self._registered_catalogs.keys())

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())


catalog_registry = CatalogRegistry()
