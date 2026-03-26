#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class PluginRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PluginRegistry, cls).__new__(cls)
            cls._instance.plugins = {}
            cls._instance.groups = {
                "Red": {},
                "Blue": {},
                "Purple": {},
                "Misc": {}
            }
        return cls._instance

    def register(self, plugin_id, name, group, tactic, description, callback):
        """
        Registers a plugin to the system.
        """
        if group not in self.groups:
            self.groups[group] = {}

        plugin_data = {
            "id": plugin_id,
            "name": name,
            "group": group,
            "tactic": tactic,
            "description": description,
            "callback": callback
        }

        self.plugins[plugin_id] = plugin_data
        
        if tactic not in self.groups[group]:
            self.groups[group][tactic] = []
        self.groups[group][tactic].append(plugin_data)

    def get_plugin(self, plugin_id):
        return self.plugins.get(plugin_id)

    def get_all(self):
        return self.plugins
        
    def get_groups(self):
        return self.groups

registry = PluginRegistry()
