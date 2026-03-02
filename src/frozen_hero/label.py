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


def print_label(row_one: str, row_two: str, date_str: str, entry_id: int) -> None:
    """Generate and print a label for a freezer entry.

    Parameters
    ----------
    row_one:    First text line (title).
    row_two:    Second text line (subtitle).
    date_str:   Best-before date as "YYYY-MM-DD".
    entry_id:   Database row id encoded in the QR code.
    """
    best_before = datetime.strptime(date_str, "%Y-%m-%d")
    label_name = _make_label_name(row_one, best_before)

    config.TMP_DIR.mkdir(parents=True, exist_ok=True)
    txt_path = config.TMP_DIR / f"{label_name}_text.png"
    qr_path = config.TMP_DIR / f"{label_name}_qr.png"
    label_path = config.TMP_DIR / f"{label_name}_label.jpg"

    try:
        _render_text_image(row_one, row_two, best_before, txt_path)
        _generate_qr_code(entry_id, qr_path)
        _compose_label(txt_path, qr_path, label_path)
        _print(label_path)
    finally:
        _cleanup(txt_path, qr_path, label_path)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _make_label_name(row_one: str, date: datetime) -> str:
    """Produce a filesystem-safe label name from the first row and date."""
    name = unicodedata.normalize("NFD", row_one).encode("ascii", "ignore").decode("ascii")
    name = "".join(c for c in name if c.isalnum())
    return name + "_" + date.strftime("%Y%m%d")


def _check_for_linebreak(text: str) -> tuple[bool, str]:
    """Split an overly-long single word across two lines if needed."""
    two_rows = len(text) > config.MAX_SUBTITLE_LEN
    if two_rows and len(text.split()) == 1:
        first = text[: config.MAX_SUBTITLE_LEN]
        second = text[config.MAX_SUBTITLE_LEN :]
        return True, f"{first} {second}"
    return two_rows, text


def _render_text_image(
    row_one: str,
    row_two: str,
    best_before: datetime,
    out_path: Path,
) -> None:
    """Render a PNG with Pango markup via ImageMagick convert."""
    two_lines, row_two = _check_for_linebreak(row_two)
    date_rise = config.PANGO_RISE_DATE_TWO_LINES if two_lines else config.PANGO_RISE_DATE

    # Escape user text before embedding in Pango/XML markup.
    safe_row_one = escape(row_one)
    safe_row_two = escape(row_two)
    date_label = escape("Haltbar bis: " + best_before.strftime("%d.%m.%Y"))

    pango_markup = (
        f'<span foreground="black" font_family="Roboto Mono" size="28000"'
        f' rise="-{config.PANGO_RISE_TITLE}">{safe_row_one}\n</span>'
        f'<span foreground="black" font_family="Roboto Mono" size="18000"'
        f' rise="-{config.PANGO_RISE_SUBTITLE}">{safe_row_two}\n</span>'
        f'<span foreground="black" font_family="Roboto Mono" size="24000"'
        f' rise="-{date_rise}">{date_label}</span>'
    )

    cmd = [
        "convert",
        "-gravity",
        "center",
        "-size",
        f"{config.TEXT_WIDTH_PX}x{config.LABEL_HEIGHT_PX}",
        f"pango:{pango_markup}",
        str(out_path),
    ]
    subprocess.run(cmd, check=True)


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
