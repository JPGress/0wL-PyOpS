from core.logger import log
import time

def run():
    print()
    log.info("--- Módulo 2: SOCMINT & Identity ---")
    log.info("Funcionalidades Piloto: Verificação de Username.")
    try:
        target = input("Insira o username do alvo: ").strip()
        if not target:
            log.warning("Operação cancelada.")
            return
        
        print()
        log.info(f"Iniciando busca SOCMINT para: {target}")
        time.sleep(1)
        log.success(f"[+] Buscando em redes sociais por '{target}'...")
        time.sleep(1.5)
        log.success(f"[+] Mapeamento de perfis concluído. (MOCK PILOTO)")
        print()
        input("Pressione Enter para voltar...")
    except KeyboardInterrupt:
        print()
        log.info("Voltando...")
