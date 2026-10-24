"""OpenHarness: the deterministic control plane for agent harnesses.

The package is standard-library only and makes no network or model calls. Every
command is a pure function of its declared inputs, so identical inputs always
produce identical bytes.
"""

from __future__ import annotations

__version__ = "0.2.0"
__all__ = ["__version__"]
