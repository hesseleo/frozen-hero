"""Centralised configuration for frozen-hero."""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Resolves to the repository root regardless of the current working directory.
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

DB_PATH: Path = PROJECT_ROOT / "database" / "frozen-hero.db"

TEMPLATES_DIR: Path = PROJECT_ROOT / "templates"
STATIC_DIR: Path = PROJECT_ROOT / "static"

TMP_DIR: Path = PROJECT_ROOT / "tmp"

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
SERVER_HOST: str = "0.0.0.0"  # noqa: S104
SERVER_PORT: int = 5000

# ---------------------------------------------------------------------------
# GPIO pins (BCM numbering)
# ---------------------------------------------------------------------------
PIN_BUZZER: int = 24       # swapped per test wiring (was 23)
PIN_LED: int = 23          # swapped per test wiring (was 24)

# ---------------------------------------------------------------------------
# Motion sensor selection
# ---------------------------------------------------------------------------
# Change to "apds9960" to use the APDS-9960 proximity sensor instead of PIR.
MOTION_SENSOR: str = "apds9960"

# PIR motion sensor
PIN_PIR: int = 18
PIN_MOTION_DEBOUNCE_US: int = 300_000

# APDS-9960 proximity sensor
PIN_APDS9960_INT: int = 4               # INT pin (active-low)
APDS9960_PROXIMITY_THRESHOLD: int = 70  # 0–255; ~10cm triggers ~110, noise ~5
APDS9960_LED_DRIVE: int = 3             # 0=100mA, 1=50mA, 2=25mA, 3=12.5mA
APDS9960_PROXIMITY_GAIN: int = 0        # 0=1x, 1=2x, 2=4x, 3=8x

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
PRINTER_ADDRESS: str = "/dev/usb/lp0"
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

# Quiet zone added by qrencode -m 1 (1 module on each side)
QR_MARGIN_PX: int = QR_CODE_SIZE

# Maximum subtitle length before it wraps to a second line
MAX_SUBTITLE_LEN: int = 32
