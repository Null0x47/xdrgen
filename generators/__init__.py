"""Auto-imports each generator submodule so `@register` populates GENERATORS."""

from __future__ import annotations

import importlib
import pkgutil

from generators.base import GENERATORS as GENERATORS

# Shared infrastructure modules — not generators.
_SKIP = {"base", "common", "device_common", "email_pool"}

for _info in pkgutil.iter_modules(__path__):
    _name = _info.name
    if _name.startswith("_") or _name in _SKIP:
        continue
    importlib.import_module(f"{__name__}.{_name}")
