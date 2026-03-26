#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pyops.py - 0wL - Python Operator's Script 
# ---------------------------------------------------------------------------------
# 0wL OPS is an advanced Python-based Operational Security toolkit tailored for
# penetration testers, red teamers, and security researchers.

from core.menu import render_menu
from core.dispatcher import Dispatcher
from plugins import load_plugins

def main():
    load_plugins()
    render_menu()
    Dispatcher.run()

if __name__ == "__main__":
    main()