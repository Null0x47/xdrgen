"""Telemetry generator registry.

Every submodule of `generators/` whose name is not in `_SKIP` is auto-imported
on package load. Each generator decorates its `generate(world)` function with
`@register("TableName")` from `generators.base`, populating `GENERATORS` as a
side effect of the import. Adding a new generator is a one-file change —
drop the file, decorate, done.
"""

from __future__ import annotations

import importlib
import pkgutil

from generators.base import GENERATORS as GENERATORS

# Submodules that contain shared infrastructure rather than a generator.
_SKIP = {"base", "common", "device_common", "email_corpus"}

for _info in pkgutil.iter_modules(__path__):
    _name = _info.name
    if _name.startswith("_") or _name in _SKIP:
        continue
    importlib.import_module(f"{__name__}.{_name}")
