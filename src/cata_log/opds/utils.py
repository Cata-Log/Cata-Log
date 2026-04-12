import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from enum import StrEnum
from functools import cached_property
from typing import override


def zulu_datetime(datetime: datetime) -> str:
    """Format a datetime to military format.

    Returns:
        The string representing the datetime in military format.
    """
    return datetime.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


class OPDSCatalog:
    """Builds an OPDS1 compatible xml catalog."""

    def __init__(
        self,
        title: str = "OPDS Catalog",
        uid: str = "root",
        updated: datetime | None = None,
    ) -> None:
        """Initialize this OPDS catalog with the minimal metadata."""
        self.metadata: list[Metadata] = [
            Metadata(zulu_datetime(updated or datetime.now()), "updated"),  # noqa: DTZ005 # tz is added by zulu_datetime anyway
            Metadata(uid, "id"),
            Metadata(title, "title"),
        ]
        self.entries: list[Entry] = []
        self.links: list[Link] = []

    @cached_property
    def xml(self) -> ET.Element:
        """Create this OPDS catalog's xml."""
        feed = ET.Element(
            "feed",
            attrib={
                "xmlns": "http://www.w3.org/2005/Atom",
                "xmlns:dc": "http://purl.org/dc/terms/",
                "xmlns:opds": "http://opds-spec.org/2010/catalog",
            },
        )
        feed.extend([link.xml for link in self.links])
        feed.extend([metadata.xml for metadata in self.metadata])
        feed.extend([entry.xml for entry in self.entries])
        return feed

    def write(self) -> bytes:
        """Write this OPDS catalog."""
        return ET.tostring(
            self.xml,
            encoding="utf-8",
            xml_declaration=True,
            short_empty_elements=True,
        )


class Metadata:
    """Builds xml metadata."""

    class Namespace(StrEnum):
        """Enum of all available namespaces."""

        DEFAULT = ""
        OPDS = "opds"
        DC = "dc"

    def __init__(
        self,
        value: str,
        name: str,
        namespace: Namespace | str = Namespace.DEFAULT,
        attributes: dict[str, str] | None = None,
    ) -> None:
        """Initialize this metadata."""
        self.namespace = namespace
        self.name = name
        self.value = value
        self.attributes = attributes or {}

    @cached_property
    def xml(self) -> ET.Element:
        """Create this metadata's xml."""
        tag = f"{self.namespace}:{self.name}" if self.namespace else self.name
        metadata_element = ET.Element(tag, attrib=self.attributes)
        metadata_element.text = self.value
        return metadata_element


class Entry:
    """Builds an OPDS entry."""

    def __init__(
        self,
        title: str,
        uid: str,
        updated: datetime | None = None,
    ) -> None:
        """Initialize this entry with the minimal metadata."""
        self.metadata: list[Metadata] = [
            Metadata(uid, "id"),
            Metadata(title, "title"),
            Metadata(zulu_datetime(updated or datetime.now()), "updated"),  # noqa: DTZ005 # tz is added by zulu_datetime anyway
        ]
        self.links: list[Link] = []

    @cached_property
    def xml(self) -> ET.Element:
        """Create this entry's xml."""
        entry_element = ET.Element("entry")
        entry_element.extend([metadata.xml for metadata in self.metadata])
        entry_element.extend([link.xml for link in self.links])
        return entry_element


class Author(Metadata):
    """Builds an author metadata element."""

    @override
    def __init__(self) -> None:
        super().__init__(name="author", value="")
        self.metadata: list[Metadata] = []

    @cached_property
    @override
    def xml(self) -> ET.Element:
        author_element = super().xml
        author_element.extend([metadata.xml for metadata in self.metadata])
        return author_element


class Link(Metadata):
    """Builds an OPDS link."""

    class Rel(StrEnum):
        """Enum for all common link relations."""

        ACQUISITION = "http://opds-spec.org/acquisition"
        SORT_NEW = "http://opds-spec.org/sort/new"
        SORT_POPULAR = "http://opds-spec.org/sort/popular"
        FEATURED = "http://opds-spec.org/featured"
        RECOMMENDED = "http://opds-spec.org/recommended"
        IMAGE_THUMBNAIL = "http://opds-spec.org/image/thumbnail"
        IMAGE = "http://opds-spec.org/image"
        SUBSECTION = "subsection"
        SELF = "self"
        START = "start"
        UP = "up"
        NEXT = "next"
        PREVIOUS = "previous"
        ALTERNATE = "alternate"
        RELATED = "related"

    def __init__(
        self,
        href: str,
        media_type: str,
        rel: Rel | str,
        attributes: dict[str, str] | None = None,
    ) -> None:
        """Initialize this link."""
        super().__init__(
            value="",
            name="link",
            attributes={
                "rel": rel,
                "href": href,
                "type": media_type,
                **(attributes or {}),
            },
        )


class ThumbnailLink(Link):
    """Builds an OPDS thumbnail link."""

    @override
    def __init__(self, href: str, media_type: str) -> None:
        super().__init__(href, media_type, rel=Link.Rel.IMAGE_THUMBNAIL)


class AcquisitionLink(Link):
    """Builds an OPDS acquisition link."""

    @override
    def __init__(self, href: str, media_type: str) -> None:
        super().__init__(href, media_type, rel=Link.Rel.ACQUISITION)


class NavigationFeedLink(Link):
    """Builds an OPDS navigation feed link."""

    @override
    def __init__(self, href: str, rel: Link.Rel | str) -> None:
        super().__init__(
            href=href,
            media_type="application/atom+xml;profile=opds-catalog;kind=navigation",
            rel=rel,
        )


class AcquistionFeedLink(Link):
    """Builds an OPDS acquisition feed link."""

    @override
    def __init__(self, href: str, rel: Link.Rel | str) -> None:
        super().__init__(
            href=href,
            media_type="application/atom+xml;profile=opds-catalog;kind=acquisition",
            rel=rel,
        )
