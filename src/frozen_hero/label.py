"""Label generation and printing for frozen-hero.

Security notes
--------------
* All external commands are executed with subprocess.run(list, shell=False) —
  no shell injection possible.
* User-supplied text is escaped with xml.sax.saxutils.escape() before being
  embedded in Pango markup — no XML/Pango injection possible.
"""

import logging
import subprocess
import unicodedata
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from frozen_hero import config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


_BEST_BEFORE: dict[str, str] = {
    "de": "Haltbar bis",
    "en": "Best before",
}

_DATE_FMT: dict[str, str] = {
    "de": "%d.%m.%y",
    "en": "%d/%m/%y",
}


def generate_label(
    row_one: str, row_two: str, date_str: str, entry_id: int, *, lang: str = "de"
) -> Path:
    """Render and compose a label image, returning the path to the JPG.

    The caller is responsible for deleting the file when done.
    Intermediate temp files (text PNG, QR PNG) are removed before returning.
    """
    best_before = datetime.strptime(date_str, "%Y-%m-%d")
    label_name = _make_label_name(row_one, best_before)

    config.TMP_DIR.mkdir(parents=True, exist_ok=True)
    txt_path = config.TMP_DIR / f"{label_name}_text.png"
    qr_path = config.TMP_DIR / f"{label_name}_qr.png"
    label_path = config.TMP_DIR / f"{label_name}_label.jpg"

    success = False
    try:
        _render_text_image(row_one, row_two, best_before, txt_path, lang)
        _generate_qr_code(entry_id, qr_path)
        _compose_label(txt_path, qr_path, label_path)
        success = True
    finally:
        _cleanup(txt_path, qr_path)
        if not success:
            _cleanup(label_path)

    return label_path


def print_label(label_path: Path) -> None:
    """Send a label image to the printer and delete it afterwards."""
    try:
        _print(label_path)
    finally:
        _cleanup(label_path)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _make_label_name(row_one: str, date: datetime) -> str:
    """Produce a filesystem-safe label name from the first row and date."""
    name = unicodedata.normalize("NFD", row_one).encode("ascii", "ignore").decode("ascii")
    name = "".join(c for c in name if c.isalnum())
    return name + "_" + date.strftime("%Y%m%d")


def _check_for_linebreak(text: str) -> str:
    """Insert a space into a single overly-long word so Pango can wrap it."""
    if len(text) > config.MAX_SUBTITLE_LEN and len(text.split()) == 1:
        return text[: config.MAX_SUBTITLE_LEN] + " " + text[config.MAX_SUBTITLE_LEN :]
    return text


def _pango_span(text: str, size: int) -> str:
    """Return a single-line Pango markup span with the project font."""
    return f'<span foreground="black" font_family="Roboto Mono" size="{size}">{escape(text)}</span>'


def _render_element(markup: str, width_px: int, tmp_path: Path) -> int:
    """Render a single Pango markup string to a PNG and return its pixel height."""
    subprocess.run(
        [
            "convert",
            "-size",
            f"{width_px}x",
            "-define",
            "pango:align=center",
            f"pango:{markup}",
            str(tmp_path),
        ],
        check=True,
    )
    result = subprocess.run(
        ["identify", "-format", "%h", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return int(result.stdout.strip())


def _render_text_image(
    row_one: str,
    row_two: str,
    best_before: datetime,
    out_path: Path,
    lang: str = "de",
) -> None:
    """Render a PNG with three composited text elements at absolute y-coordinates.

    Title top aligns with the QR code's top module row; date bottom aligns with
    the QR code's bottom module row (both offset by QR_MARGIN_PX quiet zone).
    """
    row_two = _check_for_linebreak(row_two)
    date_label = (
        _BEST_BEFORE.get(lang, _BEST_BEFORE["de"])
        + ": "
        + best_before.strftime(_DATE_FMT.get(lang, _DATE_FMT["de"]))
    )

    title_tmp = out_path.with_suffix(".title_tmp.png")
    sub_tmp = out_path.with_suffix(".sub_tmp.png")
    date_tmp = out_path.with_suffix(".date_tmp.png")

    try:
        w = config.TEXT_WIDTH_PX
        h = config.LABEL_HEIGHT_PX
        m = config.QR_MARGIN_PX

        # Render into (w - m) so both left and right have equal QR_MARGIN_PX inset.
        tw = w - m
        title_h = _render_element(_pango_span(row_one, 28000), tw, title_tmp)
        date_h  = _render_element(_pango_span(date_label, 24000), tw, date_tmp)
        if row_two:
            _render_element(_pango_span(row_two, 18000), tw, sub_tmp)

        # Title and subtitle are a visual group — keep them close together.
        # All remaining vertical space goes between the subtitle and the date.
        y_title = m
        y_sub = y_title + title_h + m
        y_date = h - m - date_h

        # Separator line: same gap above the date as the outer border around the label.
        y_sep = y_date - config.BORDER_SIZE_PX - config.QR_MARGIN_PX

        # Create white canvas, composite text elements, draw separator.
        subprocess.run(
            ["convert", "-size", f"{w}x{h}", "xc:white", str(out_path)],
            check=True,
        )
        elements = [(title_tmp, y_title), (date_tmp, y_date)]
        if row_two:
            elements.insert(1, (sub_tmp, y_sub))
        for tmp, y in elements:
            subprocess.run(
                [
                    "convert",
                    str(out_path),
                    "-gravity",
                    "NorthWest",
                    str(tmp),
                    "-geometry",
                    f"+{m}+{y}",
                    "-composite",
                    str(out_path),
                ],
                check=True,
            )
        subprocess.run(
            [
                "convert",
                str(out_path),
                "-stroke",
                "#000000",
                "-strokewidth",
                "4",
                "-draw",
                f"line {2 * m},{y_sep} {w - m},{y_sep}",
                str(out_path),
            ],
            check=True,
        )
    finally:
        _cleanup(title_tmp, sub_tmp, date_tmp)


def _generate_qr_code(entry_id: int, out_path: Path) -> None:
    """Generate a QR code PNG encoding the database entry id."""
    cmd = [
        "qrencode",
        "-o",
        str(out_path),
        "-m",
        "1",
        "-d",
        "300",
        "-s",
        str(config.QR_CODE_SIZE),
        "-l",
        "h",
        str(entry_id),
    ]
    subprocess.run(cmd, check=True)


def _compose_label(txt_path: Path, qr_path: Path, label_path: Path) -> None:
    """Combine text image and QR code, then add a border."""
    # Side-by-side composite
    subprocess.run(
        ["convert", "+append", str(txt_path), str(qr_path), str(label_path)],
        check=True,
    )
    # Add border in-place
    subprocess.run(
        [
            "convert",
            "-bordercolor",
            "black",
            "-border",
            str(config.BORDER_SIZE_PX),
            str(label_path),
            str(label_path),
        ],
        check=True,
    )


def _print(label_path: Path) -> None:
    """Send the label image to the Brother QL printer."""
    subprocess.run(
        [
            "brother_ql",
            "-m",
            config.PRINTER_MODEL,
            "-p",
            config.PRINTER_ADDRESS,
            "print",
            "-l",
            config.LABEL_WIDTH_MM,
            str(label_path),
        ],
        check=True,
    )


def _cleanup(*paths: Path) -> None:
    """Remove temporary files, ignoring missing files."""
    for p in paths:
        try:
            p.unlink()
        except FileNotFoundError:
            logger.debug("Cleanup: %s not found, skipping", p)
