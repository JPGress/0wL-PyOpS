from plugins.base import BasePlugin
from core.logger import log

from .owls_eyes_modules import (
    mod1_opsec,
    mod2_socmint,
    mod3_footprint,
    mod4_breach,
    mod5_monitor,
    mod6_socialeng,
    mod7_defensive
)

class OwlsEyesPlugin(BasePlugin):
    PLUGIN_ID = "043"
    NAME = "Personal Attack Surface Management (OwL's Eyes)"
    GROUP = "Purple"
    TACTIC = "TA0043"
    DESCRIPTION = "Ferramenta de reconhecimento e inteligência baseada no MITRE ATT&CK e OSINT."

    def run(self):
        while True:
            try:
                print()
                log.info("=== OwL's Eyes Hub ===")
                print("[1] Módulo 1: OPSEC & Infrastructure")
                print("[2] Módulo 2: SOCMINT & Identity")
                print("[3] Módulo 3: Digital Footprint & Devices")
                print("[4] Módulo 4: Breach Hunting & Credential Leaks")
                print("[5] Módulo 5: Information Monitoring")
                print("[6] Módulo 6: Social Engineering Mechanics")
                print("[7] Módulo 7: Defensive Measures")
                print("[0] Voltar ao menu principal")
                print()
                
                choice = input("OwL's Eyes > ").strip()
                
                if choice == "1":
                    mod1_opsec.run()
                elif choice == "2":
                    mod2_socmint.run()
                elif choice == "3":
                    mod3_footprint.run()
                elif choice == "4":
                    mod4_breach.run()
                elif choice == "5":
                    mod5_monitor.run()
                elif choice == "6":
                    mod6_socialeng.run()
                elif choice == "7":
                    mod7_defensive.run()
                elif choice == "0" or choice == "":
                    log.info("Saindo do OwL's Eyes...")
                    break
                else:
                    log.warning("Opção inválida.")
            except KeyboardInterrupt:
                print()
                log.info("Saindo do OwL's Eyes...")
                break
            except Exception as e:
                log.error(f"Erro na execução do módulo: {e}")
