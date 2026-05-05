"""Sink registry — each submodule exposes a `build()` factory."""

from __future__ import annotations

from sinks.base import Batch, Sink

__all__ = ["Batch", "Sink"]
