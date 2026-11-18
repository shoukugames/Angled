"""Angled - an angle-matching bubble-popping game by Shouku Games."""
from .config import VERSION as __version__  # noqa: F401

# True when running in a web browser (pygbag / WebAssembly).
import sys as _sys
WEB = _sys.platform == "emscripten"
