#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from core.config import C

class Logger:
    @staticmethod
    def info(msg):
        print(f" {C.BRIGHT_GREEN}[+]{C.RESET} {msg}")

    @staticmethod
    def warning(msg):
        print(f" {C.BRIGHT_YELLOW}[*]{C.RESET} {C.YELLOW}{msg}{C.RESET}")

    @staticmethod
    def error(msg):
        print(f" {C.BRIGHT_RED}[-]{C.RESET} {C.RED}{msg}{C.RESET}")

    @staticmethod
    def success(msg):
        print(f" {C.BRIGHT_GREEN}[+]{C.RESET} {C.GREEN}{msg}{C.RESET}")

    @staticmethod
    def debug(msg):
        print(f" {C.GRAY}[DEBUG] {msg}{C.RESET}")

log = Logger()
