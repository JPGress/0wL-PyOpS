#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from core.config import C, ascii_banner, VERSION, RELEASE, AUTHOR
from core.registry import registry
import os

def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")

def show_header():
    print(ascii_banner())
    print(f"{C.BLACK}           {C.BG_BRIGHT_RED}0wL - Python Operators Script by {AUTHOR} - v{VERSION} ({RELEASE}) {C.RESET}")
    print(f"{C.RED}+====================================================================================+{C.RESET}")
    print(f"{C.GRAY}                Select an option by entering the corresponding number{C.RESET}")
    print(f"{C.RED}+====================================================================================+{C.RESET}")

def render_menu():
    clear_screen()
    show_header()

    groups = registry.get_groups()

    order = ["Red", "Blue", "Purple", "Misc"]
    
    for group_name in order:
        tactics = groups.get(group_name, {})
        if not tactics:
            continue
            
        print(f"\n {C.BG_RED}{C.WHITE} [ {group_name.upper()} TEAM ] {C.RESET}")
        
        for tactic, plugins in tactics.items():
            for p in plugins:
                print(f"\n {C.BRIGHT_GREEN}[+]{C.RESET}{C.RED} {p['name']} [{tactic}]{C.RESET}")
                print(f"         {C.GRAY}- {p['description']}{C.RESET}")
                print(f"         {C.RED}[{p['id']}] {C.GRAY}Execute{C.RESET}")
                print(f"         {C.GRAY}---{C.RESET}")
        print()
