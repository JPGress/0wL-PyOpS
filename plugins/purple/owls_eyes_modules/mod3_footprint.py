"""Footprint real: composição dos plugins de DNS e domínio."""
from plugins.recon.dns_tools import DNSRecords, DomainIntelligence
from core.logger import log


def run():
    print("[1] Registros DNS\n[2] WHOIS e certificados\n[0] Voltar")
    choice = input("Footprint > ").strip()
    if choice == "1":
        DNSRecords().run()
    elif choice == "2":
        DomainIntelligence().run()
    elif choice not in ("", "0"):
        log.warning("Opção inválida")
