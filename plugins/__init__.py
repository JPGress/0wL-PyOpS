#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import importlib
import inspect
from core.registry import registry
from plugins.base import BasePlugin

def load_plugins():
    plugins_dir = os.path.dirname(__file__)
    for root, _, files in os.walk(plugins_dir):
        for file in files:
            if file.endswith('.py') and file != '__init__.py' and file != 'base.py':
                module_path = os.path.relpath(os.path.join(root, file), plugins_dir)
                module_name = "plugins." + module_path.replace(os.sep, '.')[:-3]
                
                try:
                    module = importlib.import_module(module_name)
                    for _, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BasePlugin) and obj is not BasePlugin:
                            # Register the plugin into the core registry
                            plugin_instance = obj()
                            registry.register(
                                plugin_id=obj.PLUGIN_ID,
                                name=obj.NAME,
                                group=obj.GROUP,
                                tactic=obj.TACTIC,
                                description=obj.DESCRIPTION,
                                callback=plugin_instance.run
                            )
                except Exception as e:
                    # Ignore silent load failures during UI startup
                    pass
