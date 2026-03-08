"""frozen-hero — Raspberry Pi freezer inventory management system."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("frozen-hero")
except PackageNotFoundError:
    __version__ = "unknown"
