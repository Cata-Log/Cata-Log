from datetime import UTC, datetime
from enum import StrEnum
from typing import override


class OPDSCatalog:
    """Builds an OPDS1 compatible xml catalog."""

    def __init__(
        self,
        title: str = "OPDS Catalog",
        uid: str = "root",
        updated: datetime = datetime.now(tz=UTC),  # noqa: B008 # should be called anew for every instance
    ) -> None:
        """Initialize this OPDS catalog with the minimal metadata."""
        self.metadata: list[Metadata] = [
            Metadata(updated.isoformat(timespec="seconds"), "updated"),
            Metadata(uid, "id"),
            Metadata(title, "title"),
        ]
        self.entries: list[Entry] = []

    def write(self) -> str:
        """Write this OPDS catalog."""
        opds_xml = """<?xml version="1.0" encoding="utf-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom"
                  xmlns:opds="http://opds-spec.org/2010/catalog">
              """
        for metadata in self.metadata:
            opds_xml += metadata.write()
        for entry in self.entries:
            opds_xml += entry.write()
        opds_xml += "</feed>"
        return opds_xml


class Metadata:
    """Builds xml metadata."""

    def __init__(self, value: str, name: str, namespace: str = "") -> None:
        """Initialize this metadata."""
        self.namespace = namespace
        self.name = name
        self.value = value

    def write(self) -> str:
        """Write this metadata."""
        tag = f"{self.namespace}:{self.name}" if self.namespace else self.name
        return f"<{tag}>{self.value}</{tag}"


class Entry:
    """Builds an OPDS entry."""

    def __init__(self, title: str, uid: str) -> None:
        """Initialize this entry with the minimal metadata."""
        self.metadata: list[Metadata] = [Metadata(uid, "id"), Metadata(title, "title")]
        self.links: list[Link] = []

    def write(self) -> str:
        """Write this OPDS entry."""
        entry_xml = "<entry>"
        for metadata in self.metadata:
            entry_xml += metadata.write()
        for link in self.links:
            entry_xml += link.write()
        entry_xml += "</entry>"
        return entry_xml


class Link:
    """Builds an OPDS link."""

    class Rel(StrEnum):
        """Enum for all link rels and their hrefs."""

        ACQUISITION = "http://opds-spec.org/acquisition"
        IMAGE_THUMBNAIL = "http://opds-spec.org/image/thumbnail"

    def __init__(self, href: str, media_type: str, rel: Rel) -> None:
        """Initialize this link."""
        self.href = href
        self.type = media_type
        self.rel = rel

    def write(self) -> str:
        """Write this link."""
        return f'<link rel="{self.rel}" href="{self.href}" type="{self.type}" />'


class ThumbnailLink(Link):
    """Builds an OPDS thumbnail link."""

    @override
    def __init__(self, href: str, type: str) -> None:
        super().__init__(href, type, rel=Link.Rel.IMAGE_THUMBNAIL)


class AcquisitionLink(Link):
    """Builds an OPDS acquisition link."""

    @override
    def __init__(self, href: str, type: str) -> None:
        super().__init__(href, type, rel=Link.Rel.IMAGE_THUMBNAIL)
