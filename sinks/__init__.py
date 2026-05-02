"""Sink registry.

Each submodule defines a sink (or a family of related sinks) plus a
`build(...)` factory that `main.py` calls when the `--sink` flag selects it.
Adding a new sink is a one-file change — drop a module here that exposes a
`build(...)` returning a `Sink`, then add a branch in `main._build_sink`.
"""

from __future__ import annotations

from sinks.base import Batch, Sink

__all__ = ["Batch", "Sink"]
