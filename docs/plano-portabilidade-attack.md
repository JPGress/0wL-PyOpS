# Portabilidade owl-ops → owl-PyOpS por ATT&CK

Data: 27/09/2026. Referência: ATT&CK Enterprise **19.2**. Este é o roteiro executável acompanhado do estado efetivo da implementação; não é uma declaração de validação de campo.

## Decisões e escopo

- Catálogo completo em lotes, Python com backends especializados e paridade de capacidades, não reprodução literal de cada subprocesso Bash.
- Linux/Kali e WSL2, com limitações de hardware/camada 2 explícitas.
- CLI `list`, `info`, `run`, `doctor`, `matrix` e menu interativo usando o mesmo parser dos plugins novos.
- IDs estáveis; aliases `ops:NNN` reproduzem a numeração da versão estável. O alias PyOpS `001` passa do mock ao motor TCP.
- Referências continuam referências. A implementação ausente do agente `1001` fica fora da migração.
- Bash estável como fonte principal; variante instável somente comparativa. Hashes e revisão de origem: [baseline](migration-baseline.json).
- Não expandir SOCMINT ou reverse shell. Preservar os IDs interativos `043`, `080` e `tcp_rev_shell`.

## Matriz de destinos

Todas as implementações abaixo estão presentes e **experimentais**. “Local” indica evidência de integração restrita a loopback ou arquivo sintético; não substitui validação em todas as plataformas. “Fixture” indica validação automatizada sem a operação real de laboratório.

| Alias OpS | ID PyOpS | ATT&CK / tipo | Implementação e evidência |
|---|---|---|---|
| 101 | `document_metadata` | T1589, T1592.002 | Python + ExifTool, entrada local/URLs/busca, CSV; integração local ExifTool e fixtures de falha. |
| 102 | `domain_intelligence` | T1596.002, T1596.003 | WHOIS e CT separados; chamadas externas reais não executadas nesta migração. |
| 103 | `reverse_dns` | T1590.002 | PTR com dnspython; DNS loopback sintético. |
| 104 | `dns_records` | T1590.002 | Registros e nomes fornecidos; DNS loopback, NXDOMAIN, timeout. |
| 105 | `search_queries` | T1593.002 | Geração de URLs, exportação e navegador opcional; teste offline de codificação e CLI. |
| 106 | `website_inventory` | T1594, T1590.002, T1596.002 | Links relativos/deduplicação e enriquecimento selecionado; HTTP loopback e fixtures. |
| 201 | `dns_zone_transfer` | T1590.002 | AXFR com dnspython; fixture de recusa. Integração AXFR real pendente. |
| 202 | `cname_inventory` | T1590.002 | Inventário de aliases/resolução; fixture. Não confirma takeover. |
| 301 | `wireless_lab` | T1040 / T1110.002 por operação | Descoberta/captura, deauth delimitado e cracking offline separados; limpeza testada por mocks; hardware pendente. |
| 601 | `root_recovery_reference` | Referência | Guia administrativo; sem execução de alteração de boot/senha. |
| 602 | `local_exposure_audit` | T1082, T1083 | Coletores compartilhados de inventário, filesystem e capabilities; conteúdo sensível não copiado automaticamente. |
| 603 | `vim_reference` | Referência | Edição, navegação e saída; sem execução. |
| 604 | `restricted_shell_reference` | Referência | Limitações e escapes para consulta; sem execução. |
| 801 | `arp_mitm_lab` | T1557.002, T1040 | Processos delimitados, PCAP, restauração de forwarding; falha e cancelamento testados por mocks. |
| 901, 902 | `tcp_scan` | T1046 interno / T1595 externo | Motor único Python com limite de concorrência; TCP loopback e estados de falha. |
| 903 | `http_headers` | T1046 interno / T1595 externo | HEAD, TLS, status/redirecionamento; HTTP loopback e bloqueio/TLS por fixture. |
| 904 | `smb_inventory` | T1046, T1135 / T1595, T1595.002 externos | Perfis shares/services/rpc/vulnerabilities; fixture de acesso negado, argumentos e autenticação. Laboratório SMB pendente. |
| 905 | `linux_inventory` | T1082 principal | Sistema, contas, interfaces, rotas, sockets, processos e serviços por seção. |
| 906 | `filesystem_audit` | T1083 | Raízes explícitas, limites, permissões/proprietários; árvore sintética e ciclo de symlink. |
| 907 | `find_reference` | Referência T1083 | Exemplos consultáveis; não conta como cobertura operacional. |
| 908 | `nmap_scan` | T1046 interno / T1595 externo | TCP connect, XML e resumo; Nmap real contra fixture loopback. |
| 909 | `arp_discovery` | T1018 | Backend arp-scan sem fallback ICMP disfarçado; integração de camada 2 pendente. |
| 001 | `network_reference` | Referência | Comandos de consulta Linux. |
| 002 | `windows_reference` | Referência | Comandos Windows para consulta no Linux. |
| 003 | `wsl_vbox_routes` | Utilitário | plan/apply/revert, journal e rollback; conflito/rollback por mocks. Topologia WSL/VBox pendente. |
| 1001 | `legacy_arp_agent` | Lacuna | Alias resolve, mas a execução retorna indisponibilidade; não há agente funcional de origem. |
| 000 | Sair | Interface | Não é plugin nem técnica. |

Resultado estrutural: **27 opções legadas endereçadas** (excluindo sair), com 901/902 consolidadas em um motor: 19 plugins operacionais novos, seis referências e uma lacuna. Somados aos três plugins interativos preservados, o loader registra 29 entradas e 28 aliases, incluindo `001`.

A [matriz ATT&CK gerada](matriz-attack.md) registra o catálogo desta entrega; gere novamente pelo comando `matrix` após modificar metadados.

## Correções de classificação e diferenças intencionais

- AXFR é coleta de DNS ([T1590.002](https://attack.mitre.org/techniques/T1590/002/)), não comprometimento de servidor DNS.
- CT/crt.sh corresponde a [certificados digitais](https://attack.mitre.org/techniques/T1596/003/); não foi renomeado um provedor CT como DNS passivo.
- A detecção de CNAME não confirma tomada de domínio. A ferramenta foi nomeada conforme o comportamento real.
- O contexto de scanning determina [T1046](https://attack.mitre.org/techniques/T1046/) ou [T1595](https://attack.mitre.org/techniques/T1595/). Os números legados não determinam táticas.
- Wireless não usa T1566 (phishing). Captura e análise offline são associadas a T1040 e T1110.002; etapas auxiliares não recebem técnica artificialmente.
- JALESC/inventários relatam exposição, não execução de elevação de privilégios. Conteúdo de históricos e credenciais não é copiado automaticamente.
- O scanner Nmap usa TCP connect, sem privilégios e sem descoberta prévia de host; os alvos e portas são explícitos. O comportamento corrige a integração em que o backend terminava com zero hosts classificados como ativos.
- A enumeração SMB consolida wrappers redundantes em smbclient, rpcclient e Nmap. O perfil padrão é shares; `all` inclui shares/services/rpc, não vulnerabilidades. O perfil opcional de vulnerabilidades usa a verificação MS17-010, sem prometer todos os checks históricos.
- Wireless cria uma interface monitor temporária se necessário, sem encerrar gerenciadores de rede ou alterar MACs automaticamente. Exige identificar o canal original para restauração.
- Rotas são aplicadas no estado de execução do Linux, sem anexar configuração persistente a `/etc/sysctl.conf`. `revert` usa o journal da execução. Instruções Windows não presumem que seu gateway seja igual ao do Linux.
- Guias foram organizados e resumidos por capacidade. Helpers Bash de Tor/proxy não foram transformados em promessa de anonimato nem acionados automaticamente.

## Lotes e aceite

| Lote | Entrega implementada | Aceite restante |
|---|---|---|
| 0 | Baseline, decisões e matriz de destinos. | Nenhum estrutural. |
| 1 | Contrato, CLI, aliases, loader, subprocessos, JSON, dependências, testes e higiene do Git. | Exercitar também Python 3.11 e outras instalações Linux/WSL2 antes de declarar suporte integral. |
| 2 | DNS, PTR, WHOIS/CT, AXFR, CNAME. | WHOIS/CT e AXFR em laboratório apropriado. |
| 3 | HTTP, links, buscas e ExifTool/CSV. | Revisão de busca externa, sujeita a bloqueios; arquivos/URLs independem dessa descoberta. |
| 4 | TCP, Nmap/XML e ARP. | ARP em segmento de laboratório; outras topologias/versões de backend. |
| 5 | Inventário local, filesystem, JALESC e guias. | Integração abrangente dos coletores entre distribuições e níveis de privilégio. |
| 6 | Perfis SMB. | Samba/Windows de laboratório: compartilhamentos, RPC, autenticação e perfis adicionais. |
| 7 | Rotas e MITM com limpeza. | VM/topologia descartável para comprovar restauração real. |
| 8 | Operações wireless separadas e limpeza. | Adaptador físico compatível e PCAP de laboratório; não executar em redes externas. |
| 9 | Documentação, matriz, aliases e footprint real integrado ao OwL’s Eyes. | Promoção a `ready` somente depois dos aceites ambientais respectivos. |

Nenhum plugin recebeu `ready` apenas porque seus testes unitários passaram. A implementação foi entregue, mas a validação operacional integral permanece aberta nos itens acima.

## Interfaces e dados

`run <id> --help` é a referência dos parâmetros de cada ferramenta. Chamadas incompletas não abrem prompts. Plugins antigos com apenas `run()` retornam código 3 quando invocados pela CLI não interativa.

O resultado JSON tem versão 1, ID, estado, horários, parâmetros sem chaves de senha/token, associações ATT&CK, achados, erros e artefatos existentes. `outputs/<id>/<uuid>/` separa execuções e está fora do Git. XML Nmap, CSV ExifTool e PCAP permanecem disponíveis como artefatos especializados.

Subprocessos não usam shell. SIGINT/SIGTERM permitem finalizar a operação e escrever resultados parciais. A limpeza limita-se aos processos/interfaces criados pela execução. Falhas de restauração são reportadas, não escondidas. SIGKILL, desligamento e mudanças administrativas concorrentes exigem recuperação pelo journal.

## Validação reproduzível

```sh
python -m pytest -q
python -m pytest -q -m integration
python pyops.py doctor
python pyops.py matrix --format json
python -m pip wheel --no-deps --no-build-isolation --wheel-dir /tmp/owl-pyops-wheels .
```

**Resultado registrado:** 58 testes unitários e seis integrações locais passaram.

A suíte unitária cobre registro atômico, aliases, falhas de importação, argumentos, JSON, processos, timeouts, DNS/HTTP, parsers, saídas privadas e restauração simulada. A integração é opt-in: HTTP/TCP/DNS em loopback, Nmap contra uma porta sintética e ExifTool em arquivo sintético.

Ambiente observado: Python 3.14.7, pytest 9.1.1, dnspython 2.8.0, requests 2.34.2, beautifulsoup4 4.15.0, Nmap 7.99 e ExifTool 13.55. O wheel foi construído sem instalar dependências ou acessar índices externos.

O sandbox bloqueou sockets no primeiro ensaio. A repetição autorizada fora dele continuou restrita a `127.0.0.1`. Não houve varredura de alvos externos, operação MITM/deauth, mudança real de rotas, coleta SOCMINT ou alteração nos scripts Bash.

## Próximo aceite para outro agente

1. Executar as suítes acima no ambiente alvo e registrar versões/resultados.
2. Para cada linha experimental, preparar a fixture de laboratório indicada e verificar sucesso, falha e interrupção, incluindo ausência de processos/rotas/interfaces residuais.
3. Registrar diferenças de plataforma e evidência neste documento; promover somente o plugin validado a `ready`.
4. Manter `legacy_arp_agent` indisponível. Sua implementação seria um trabalho novo, fora da portabilidade acordada.

Fonte da versão: [histórico oficial do MITRE](https://attack.mitre.org/resources/versions/). A matriz é um inventário de comportamentos associados, não um certificado de cobertura completa de técnicas.
