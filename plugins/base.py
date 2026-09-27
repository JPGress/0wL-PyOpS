#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import importlib.util
import json
import shutil
from dataclasses import asdict


class BasePlugin:
    PLUGIN_ID = ""
    NAME = ""
    GROUP = ""  # Red, Blue, Purple, Misc
    TACTIC = ""
    DESCRIPTION = ""
    ALIASES = ()
    KIND = "tool"
    STATUS = "experimental"
    ATTACK = ()
    DEPENDENCIES = ()
    OPERATION_DEPENDENCIES = {}
    OPERATION_KEY = "operation"
    UNAVAILABLE_REASON = ""

    def unavailable(self, parameters=None):
        reasons = [self.UNAVAILABLE_REASON] if self.UNAVAILABLE_REASON else []
        dependencies = self.DEPENDENCIES + self.OPERATION_DEPENDENCIES.get((parameters or {}).get(self.OPERATION_KEY), ())
        for kind, name in dependencies:
            if kind == "executable" and not shutil.which(name):
                reasons.append(f"Executável ausente: {name}")
            elif kind == "python":
                try:
                    found = importlib.util.find_spec(name)
                except ModuleNotFoundError:
                    found = None
                if found is None:
                    reasons.append(f"Pacote Python ausente: {name}")
        return reasons

    def add_arguments(self, parser):
        pass

    def parser(self):
        parser = argparse.ArgumentParser(prog=self.PLUGIN_ID, description=self.DESCRIPTION)
        self.add_arguments(parser)
        return parser

    def execute(self, parameters, context):
        raise NotImplementedError("Este plugin oferece somente interface interativa")

    @property
    def automated(self):
        return type(self).execute is not BasePlugin.execute

    def run(self):
        """
        Executes the main entry point logic of the plugin.
        Should be implemented by subclasses.
        """
        import shlex
        from core.operations import execute
        parser = self.parser()
        parser.print_help()
        try:
            parameters = vars(parser.parse_args(shlex.split(input("Argumentos (Ctrl+C cancela): "))))
        except SystemExit:
            return
        result = execute(self, parameters)
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
