#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from core.config import C
from core.registry import registry
from core.logger import log

class Dispatcher:
    @staticmethod
    def read_option():
        try:
            option = input(f"\n {C.BRIGHT_GREEN}[>]{C.RESET} {C.GREEN}ID ou alias (000 para sair): {C.RESET}").strip()
            return option
        except KeyboardInterrupt:
            return "000"
        except EOFError:
            return "000"

    @staticmethod
    def run():
        while True:
            option = Dispatcher.read_option()
            
            if option == "000":
                log.info("Exiting...")
                break
                
            plugin = registry.get_plugin(option)
            if plugin:
                print(f"\n{C.BRIGHT_GREEN}[+]{C.RESET} Selected: {plugin['name']}")
                try:
                    plugin['callback']()
                except (KeyboardInterrupt, EOFError):
                    log.info("Operação cancelada.")
                except Exception as e:
                    log.error(f"Plugin execution failed: {e}")
                from core.menu import render_menu
                render_menu()
            else:
                log.warning("Invalid option. Please try again.")
