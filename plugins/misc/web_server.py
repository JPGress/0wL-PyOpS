#!/usr/bin/env python3

# Basic Web Server for OwL-PyOpS

import socket
import http.server
import socketserver
import os
from pathlib import Path
from functools import partial
from plugins.base import BasePlugin
from core.logger import log

class WebServer(BasePlugin):
    # Metadados lidos pelo core/registry.py
    PLUGIN_ID = "080"
    DEPENDENCIES = (("executable", "ip"),)
    NAME = "Web Server"
    GROUP = "Misc"
    TACTIC = "Utilities"
    DESCRIPTION = "Usa um servidor web embutido para servir arquivos estáticos."

    def __init__(self):
        super().__init__()

    def run(self):
        log.info("Iniciando configuração do Servidor Web...")
        ip = self.select_interface()
        if not ip:
            log.warning("Configuração de interface cancelada.")
            return

        port = self.select_port()
        if not port:
            log.warning("Configuração de porta cancelada.")
            return

        value = input("[>] Diretório a publicar (obrigatório): ").strip()
        if not value:
            log.error("Informe um diretório explicitamente")
            return
        directory = Path(value).expanduser()
        if not directory.is_dir():
            log.error("Diretório inválido")
            return
        self.start_server(ip, port, directory.resolve())

    def select_interface(self):
        from core.operations import command
        import json
        try:
            raw, _, _ = command(["ip", "-json", "address", "show"])
            active_interfaces = [(item["ifname"], address["local"])
                                 for item in json.loads(raw)
                                 for address in item.get("addr_info", [])
                                 if address.get("family") == "inet"]
        except Exception as exc:
            log.error(f"Não foi possível listar interfaces: {exc}")
            return None

        if not active_interfaces:
            log.error("Nenhuma interface de rede com IPv4 encontrada.")
            return None

        print("\n[ Interfaces de Rede Ativas ]\n")
        for idx, (iface, ip) in enumerate(active_interfaces):
            print(f"  [{idx + 1}] {iface} - {ip}")
        print(f"  [0] Cancelar\n")

        while True:
            choice = input("[>] Escolha o número da interface: ").strip()
            if choice == "0":
                return None
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(active_interfaces):
                    selected_iface, selected_ip = active_interfaces[choice_idx]
                    log.info(f"Interface selecionada: {selected_iface} ({selected_ip})")
                    return selected_ip
                else:
                    log.warning("Opção inválida. Tente novamente.")
            except ValueError:
                log.warning("Entrada inválida. Digite um número.")

    def select_port(self):
        print("\n[ Configuração de Porta ]\n")
        while True:
            choice = input("[>] Digite a porta a ser utilizada (ex: 8000) ou 0 para cancelar: ").strip()
            if choice == "0":
                return None
            try:
                port = int(choice)
                if 1 <= port <= 65535:
                    log.info(f"Porta {port} selecionada.")
                    return port
                else:
                    log.warning("A porta deve estar entre 1 e 65535.")
            except ValueError:
                log.warning("Entrada inválida. Digite um número válido.")

    def start_server(self, ip, port, directory):
        # Servidor estático básico usando http.server do Python
        Handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
        
        current_dir = str(directory)
        print()
        log.info(f"Diretório base: {current_dir}")
        log.success(f"Servidor disponível em: http://{ip}:{port}/")
        print()
        
        try:
            # Reutilizar porta para evitar o erro 'Address already in use' ao reiniciar rápido
            socketserver.TCPServer.allow_reuse_address = True
            with socketserver.TCPServer((ip, port), Handler) as httpd:
                log.info("Servidor no ar. Pressione Ctrl+C para encerrar.")
                httpd.serve_forever()
        except OSError as e:
            log.error(f"Erro ao iniciar o servidor na porta {port}: {e}")
        except KeyboardInterrupt:
            print()
            log.info("Encerrando o servidor web...")
