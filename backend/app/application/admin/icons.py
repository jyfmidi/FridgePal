"""Admin icon upload validation and SVG sanitization.

Uploaded icons are stored as data URIs on the FoodDefinition. SVG content is
sanitized with an element allow-list (drawing primitives only) and attribute
stripping (no event handlers, styles, external references, or scripting), and
the client renders icons through an ``<img>`` element, so a hostile upload can
never execute script in the application. PNG uploads are accepted only when
their magic bytes match.
"""

import base64
import re
import xml.etree.ElementTree as ET
from typing import Final

MAX_ICON_BYTES: Final = 100 * 1024  # 100 KB

PNG_MAGIC: Final = b"\x89PNG\r\n\x1a\n"
SVG_MIME = "image/svg+xml"
PNG_MIME = "image/png"

# Drawing and gradient elements only; anything that can reference or execute
# external content (script, image, use, foreignObject, style, a, iframe,
# object, embed, animate, audio, video) is rejected outright.
_ALLOWED_SVG_TAGS: Final = frozenset(
    {
        "svg",
        "g",
        "defs",
        "symbol",
        "path",
        "circle",
        "rect",
        "ellipse",
        "line",
        "polyline",
        "polygon",
        "linearGradient",
        "radialGradient",
        "stop",
        "clipPath",
        "mask",
        "pattern",
        "marker",
        "title",
        "desc",
        "text",
        "tspan",
        "filter",
        "feBlend",
        "feColorMatrix",
        "feComponentTransfer",
        "feComposite",
        "feFlood",
        "feFuncA",
        "feFuncB",
        "feFuncG",
        "feFuncR",
        "feGaussianBlur",
        "feMerge",
        "feMergeNode",
        "feOffset",
        "feTile",
        "feDisplacementMap",
    }
)

# Presentation and geometry attributes that a simple food illustration needs.
_ALLOWED_SVG_ATTRS: Final = frozenset(
    {
        "xmlns",
        "xmlns:xlink",
        "viewBox",
        "width",
        "height",
        "preserveAspectRatio",
        "d",
        "cx",
        "cy",
        "r",
        "rx",
        "ry",
        "x",
        "y",
        "x1",
        "y1",
        "x2",
        "y2",
        "points",
        "transform",
        "fill",
        "fill-rule",
        "fill-opacity",
        "stroke",
        "stroke-width",
        "stroke-linecap",
        "stroke-linejoin",
        "stroke-miterlimit",
        "stroke-dasharray",
        "stroke-opacity",
        "opacity",
        "vector-effect",
        "shape-rendering",
        "offset",
        "stop-color",
        "stop-opacity",
        "gradientUnits",
        "gradientTransform",
        "spreadMethod",
        "clip-path",
        "clip-rule",
        "mask",
        "patternUnits",
        "patternTransform",
        "font-size",
        "font-family",
        "font-weight",
        "text-anchor",
        "dominant-baseline",
    }
)

_EXTERNAL_REF = re.compile(r"url\(\s*(?!\s*#)", re.IGNORECASE)


class IconValidationError(Exception):
    """Raised when an icon upload fails validation or sanitization."""

    def __init__(self, message: str, *, code: str = "ADMIN_ICON_INVALID") -> None:
        super().__init__(message)
        self.code = code


def _sanitize_element(element: ET.Element) -> ET.Element | None:
    tag = element.tag.split("}")[-1] if isinstance(element.tag, str) else ""
    if tag not in _ALLOWED_SVG_TAGS:
        return None
    cleaned = ET.Element(element.tag)
    for key, value in element.attrib.items():
        name = key.split("}")[-1].lower()
        if name not in _ALLOWED_SVG_ATTRS:
            continue
        if _EXTERNAL_REF.search(value):
            continue
        cleaned.set(key, value)
    for child in element:
        cleaned_child = _sanitize_element(child)
        if cleaned_child is not None:
            cleaned.append(cleaned_child)
    if element.text and element.text.strip():
        cleaned.text = element.text
    return cleaned


def sanitize_svg(content: str) -> str:
    """Return a safe SVG string containing only allow-listed elements/attributes."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as error:
        raise IconValidationError(
            "The uploaded SVG could not be parsed.", code="ADMIN_ICON_INVALID"
        ) from error
    cleaned = _sanitize_element(root)
    if cleaned is None or cleaned.tag.split("}")[-1] != "svg":
        raise IconValidationError(
            "The uploaded file is not a usable SVG.", code="ADMIN_ICON_INVALID"
        )
    # Serialize with the standard SVG namespace unprefixed (no `ns0:` noise).
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    return ET.tostring(cleaned, encoding="unicode")


def build_icon_data_uri(mime: str, content: bytes) -> str:
    return f"data:{mime};base64,{base64.b64encode(content).decode('ascii')}"


def validate_icon_upload(filename: str, content_type: str, content: bytes) -> str:
    """Validate and sanitize an uploaded icon; returns the stored data URI."""
    if len(content) > MAX_ICON_BYTES:
        raise IconValidationError(
            "Icons must be at most 100 KB.", code="ADMIN_ICON_TOO_LARGE"
        )
    if len(content) == 0:
        raise IconValidationError("The uploaded file is empty.", code="ADMIN_ICON_INVALID")

    if filename.lower().endswith(".png") or content_type == PNG_MIME:
        if not content.startswith(PNG_MAGIC):
            raise IconValidationError(
                "The uploaded file is not a PNG image.", code="ADMIN_ICON_INVALID"
            )
        return build_icon_data_uri(PNG_MIME, content)

    if filename.lower().endswith(".svg") or content_type in (
        SVG_MIME,
        "text/xml",
        "text/plain",
    ):
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise IconValidationError(
                "The uploaded SVG is not valid UTF-8 text.", code="ADMIN_ICON_INVALID"
            ) from error
        if "<svg" not in text.lower():
            raise IconValidationError(
                "The uploaded file is not an SVG image.", code="ADMIN_ICON_INVALID"
            )
        safe = sanitize_svg(text)
        return build_icon_data_uri(SVG_MIME, safe.encode("utf-8"))

    raise IconValidationError(
        "Icons must be SVG or PNG files.", code="ADMIN_ICON_INVALID"
    )
