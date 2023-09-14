from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "ZmlError",
    "ZmlNameError",
    "ZmlSemanticsError",
]


def _generate_error_text(start: str, expected_type: str, tag: str, context: str) -> str:
    """Generates a generic error message."""

    buff = f"{start} {expected_type} {tag!r}"

    if context is None:
        return buff + "."

    return buff + f": {context}"


class ZmlError(BaseException):
    """An error raised from ZML."""


@dataclass
class ZmlNameError(ZmlError):
    """Raised when an unknown tag is used."""

    tag: str
    context: str | None = None
    expected_type: str = "tag"

    def __str__(self) -> str:
        return _generate_error_text(
            "Unknown", self.expected_type, self.tag, self.context or ""
        )


@dataclass
class ZmlSemanticsError(ZmlError):
    """Raised when a semantic error occurs, such as unsetting a macro that isn't set."""

    tag: str
    context: str | None = None
    expected_type: str = "tag"

    def __str__(self) -> str:
        return _generate_error_text(
            "Invalid", self.expected_type, self.tag, self.context or ""
        )
