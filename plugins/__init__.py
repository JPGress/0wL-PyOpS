"""Descoberta sem operações externas e sem falhas silenciosas."""
import importlib
import inspect
from pathlib import Path
from core.registry import registry
from plugins.base import BasePlugin


def load_plugins():
    registry.clear()
    root = Path(__file__).parent
    for path in sorted(root.rglob("*.py")):
        if path.name in ("__init__.py", "base.py"):
            continue
        name = "plugins." + ".".join(path.relative_to(root).with_suffix("").parts)
        try:
            module = importlib.import_module(name)
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if cls.__module__ != name or not issubclass(cls, BasePlugin) or cls is BasePlugin:
                    continue
                if not cls.PLUGIN_ID:
                    continue
                try:
                    plugin = cls()
                    registry.register(plugin.PLUGIN_ID, plugin.NAME, plugin.GROUP,
                                      plugin.TACTIC, plugin.DESCRIPTION, plugin.run, plugin)
                except Exception as exc:
                    registry.errors.append(f"{name}.{cls.__name__}: {exc}")
        except Exception as exc:
            registry.errors.append(f"{name}: {exc}")
    return registry
