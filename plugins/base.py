#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class BasePlugin:
    PLUGIN_ID = ""
    NAME = ""
    GROUP = ""  # Red, Blue, Purple, Misc
    TACTIC = ""
    DESCRIPTION = ""

    def run(self):
        """
        Executes the main entry point logic of the plugin.
        Should be implemented by subclasses.
        """
        raise NotImplementedError("Plugin must implement run() method.")
