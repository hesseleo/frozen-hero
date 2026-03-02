"""Centralised configuration for frozen-hero."""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Resolves to the repository root regardless of the current working directory.
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

DB_PATH: Path = PROJECT_ROOT / "database" / "frozen-hero.db"

TEMPLATES_DIR: Path = PROJECT_ROOT / "templates"
STATIC_DIR: Path = PROJECT_ROOT / "images"

TMP_DIR: Path = PROJECT_ROOT / "tmp"

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
SERVER_HOST: str = "127.0.0.1"
SERVER_PORT: int = 5000

# ---------------------------------------------------------------------------
# GPIO pins (BCM numbering)
# ---------------------------------------------------------------------------
PIN_MOTION_DETECTOR: int = 18
PIN_BUZZER: int = 23
PIN_LED: int = 24

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
CAMERA_RESOLUTION: tuple[int, int] = (640, 480)

# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------
SCAN_TIMEOUT_SECONDS: float = 5.0
BUZZER_BEEP_SECONDS: float = 0.1

# ---------------------------------------------------------------------------
# Printer
# ---------------------------------------------------------------------------
PRINTER_MODEL: str = "QL-580N"
PRINTER_ADDRESS: str = "usb://04f9:20c0/000D0Z248231"
LABEL_WIDTH_MM: str = "62"

# ---------------------------------------------------------------------------
# Label layout
# ---------------------------------------------------------------------------
# QR code size: each module is qrcodeSize pixels wide (px = size * 23).
QR_CODE_SIZE: int = 10
PRINTABLE_WIDTH_PX: int = 696
BORDER_SIZE_PX: int = 5

# Derived label dimensions
_QR_HEIGHT_PX: int = 23 * QR_CODE_SIZE
TEXT_WIDTH_PX: int = PRINTABLE_WIDTH_PX - _QR_HEIGHT_PX - (2 * BORDER_SIZE_PX)
LABEL_HEIGHT_PX: int = _QR_HEIGHT_PX

# Pango text positioning (rise values in Pango units)
PANGO_SCALE: int = 512
_SMALL_SPACE: int = int(_QR_HEIGHT_PX / 6) * PANGO_SCALE
PANGO_RISE_TITLE: int = _SMALL_SPACE
PANGO_RISE_SUBTITLE: int = 2 * _SMALL_SPACE
PANGO_RISE_DATE: int = int(4.8 * _SMALL_SPACE)
# When subtitle wraps to two lines, move the date up to avoid overlap.
PANGO_RISE_DATE_TWO_LINES: int = 3 * _SMALL_SPACE

# Maximum subtitle length before it wraps to a second line
MAX_SUBTITLE_LEN: int = 32
