from pydantic.dataclasses import dataclass


@dataclass(frozen=True, validate_on_init=True)
class Configuration:
    """Dataclass of a provider configuration."""

    name: str
    helptext: str
    default: str | None = None

    def info(self) -> dict[str, str | None]:
        """Get information about the configuration."""
        return {
            "name": self.name,
            "helptext": self.helptext,
            "default": self.default,
        }
