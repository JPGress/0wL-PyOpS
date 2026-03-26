from core.logger import log
import time

def run():
    print()
    log.info("--- Módulo 3: Digital Footprint & Devices ---")
    log.info("Funcionalidades Piloto: Rastreamento de Domínios.")
    try:
        domain = input("Insira o domínio alvo: ").strip()
        if not domain:
            log.warning("Operação cancelada.")
            return
        
        print()
        log.info(f"Iniciando análise de Digital Footprint para: {domain}")
        time.sleep(1)
        log.success(f"[+] Consultando registros DNS e WHOIS para '{domain}'...")
        time.sleep(1.5)
        log.success(f"[+] Subdomínios e IPs associados encontrados. (MOCK PILOTO)")
        print()
        input("Pressione Enter para voltar...")
    except KeyboardInterrupt:
        print()
        log.info("Voltando...")
