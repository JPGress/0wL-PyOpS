# OwL's Eyes - Documentação dos Módulos

Este repositório interno contém as implementações compartimentadas que formam o hub do `OwL's Eyes`, uma ferramenta desenhada para reconhecimento, OSINT, e gestão de superfície de ataque pessoal (PASM).

## Módulos do Sistema:
- **`mod1_opsec.py`**: Gerenciamento de Identidades e Evasão.
- **`mod2_socmint.py`**: Inteligência em Mídias Sociais (SOCMINT). Ferramentas chave: Sherlock, Maigret, WhatsMyName. (MVP Funcional).
- **`mod3_footprint.py`**: Rastreio de Infraestrutura e Pegada Digital. Ferramentas chave: WHOIS e DNS. (MVP Funcional).
- **`mod4_breach.py`**: Busca de Vazamentos. Ferramentas chave: Have I Been Pwned, DeHashed. 
- **`mod5_monitor.py`**: Monitoramento Ativo e Alertas.
- **`mod6_socialeng.py`**: Mecânicas de Engenharia Social Aplicada.
- **`mod7_defensive.py`**: Recomendações Defensivas e Remediações.

## Execução:
Por se tratar de um plugin do ecossistema PyOpS, nenhum módulo aqui deve ser executado de forma "solta" no terminal (`python3 mod2_socmint.py`). O entrypoint `pyops.py` e o loader `owls_eyes.py` se encarregam de fornecer orquestração, segurança de log e captura de erros para cada componente de forma centralizada.
