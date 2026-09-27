# Manual do operador — OwL PyOpS 0.2.0

Manual operacional em português para operadores experientes em Linux e segurança. Referência conferida contra o código e os parsers locais da versão de pacote **0.2.0**. Todos os exemplos são instruções para execução posterior em ambiente autorizado; a elaboração deste documento não executou varreduras externas, SOCMINT, MITM, deauth ou alterações de rede.

<a id="sumario"></a>
## Sumário

1. [Versão e escopo](#escopo)
2. [Instalação e ambiente](#instalacao)
3. [Menu, IDs e cancelamento](#interface)
4. [Referência da CLI](#cli)
5. [Catálogo das 29 entradas](#catalogo)
6. [Fluxos operacionais](#fluxos)
7. [Preparação e restauração do laboratório](#laboratorio)
8. [Resultados e automação](#resultados)
9. [ATT&CK e migração OpS](#migracao)
10. [Diagnóstico e manutenção](#diagnostico)

<a id="escopo"></a>
## 1. Versão e escopo

O pacote declara `0.2.0` em [pyproject.toml](../pyproject.toml). O banner ainda lê `VERSION = "0.01.000"` e `RELEASE = "BOIDAE"` de [core/config.py](../core/config.py); essa divergência é de apresentação. Não existe opção `--version` na CLI atual.

O PyOpS é uma implementação modular em Python, sucessora do OpS Bash. Não executa o monólito Bash como backend: algumas ferramentas chamam executáveis específicos. O catálogo contém 29 entradas: 19 ferramentas automatizáveis implementadas, seis referências consultáveis, três plugins antigos exclusivamente interativos e uma lacuna automatizável apenas no sentido de devolver indisponibilidade. Todas as entradas têm estado `experimental`. Presença no catálogo, dependências instaladas, resultado `success` e testes locais não equivalem a validação operacional nem a cobertura integral de uma técnica ATT&CK.

As capacidades implementadas incluem DNS, WHOIS/CT, inventário web, metadados, TCP/Nmap/ARP, inventário Linux, indicadores de arquivos, SMB e operações delimitadas de laboratório. Recuperação root e shells restritos são referências; não são automações de exploração. `legacy_arp_agent` continua sem implementação. Os módulos 1, 4, 5, 6 e 7 do OwL's Eyes são indisponíveis.

<a id="instalacao"></a>
## 2. Instalação e ambiente

Execute a partir de `owl-PyOpS/`, com Python 3.11 ou superior e suporte a `venv`:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dns,web,dev]'
python pyops.py doctor
pyops list
```

`pyops` é o comando instalado, apontando para `core.cli:main`; `python pyops.py` usa o script do checkout. Os exemplos abaixo usam o script, a partir dessa pasta. O diretório corrente determina os caminhos relativos de entrada e saída, mesmo usando o comando instalado. Não é necessário instalar dependências globais ou usar `--break-system-packages`.

| Extra | Bibliotecas declaradas | Uso |
|---|---|---|
| `dns` | dnspython >=2.6,<3 | DNS, PTR, CNAME, AXFR |
| `web` | requests >=2.31,<3; beautifulsoup4 >=4.12,<5 | HTTP e HTML |
| `socmint` | instaloader >=4.12,<5; requests; beautifulsoup4 | Módulo 2 do `043` |
| `dev` | pytest >=8,<10; dnspython; requests; beautifulsoup4 | Testes |
| `all` | Bibliotecas de DNS, web e SOCMINT | Funcionalidades opcionais; não inclui pytest |

O núcleo usa a biblioteca padrão. Pacotes opcionais ausentes não removem a entrada do catálogo. Para todas as bibliotecas e testes, instale `'.[all,dev]'` no mesmo ambiente virtual.

| Executável / requisito | Ferramentas que o utilizam |
|---|---|
| `whois` | `domain_intelligence`; enriquecimento de `website_inventory` |
| `exiftool` | `document_metadata`, inclusive para arquivos locais |
| `nmap` | `nmap_scan`; SMB `services`, `vulnerabilities`, `all` |
| `smbclient`, `rpcclient` | Respectivamente SMB `shares` e `rpc`; ambos em `all` |
| `ip` (iproute2) | `080`, rotas, wireless; inventário Linux |
| `ss`, `ps`, `systemctl` | Inventário Linux e exposição local, por seção |
| `getcap` | `local_exposure_audit` |
| `arp-scan` | `arp_discovery` |
| `arpspoof`, `tcpdump` | `arp_mitm_lab` |
| `iw`, `ip`, `airodump-ng` | Wireless `discover`/`capture` |
| `iw`, `ip`, `aireplay-ng` | Wireless `deauth` |
| `aircrack-ng` | Wireless `crack` |

Instale os backends pelo gerenciador de pacotes da distribuição. `doctor` verifica presença, não instala pacotes. Inventário local não declara todos os executáveis em seus metadados: falhas são registradas por seção. O enriquecimento web também verifica DNS/WHOIS somente durante a execução. SOCMINT faz sua própria checagem no módulo.

No WSL2, confirme interfaces em `doctor` e `ip -br address`, rotas em `ip route show`, DNS em `/etc/resolv.conf` e os serviços realmente disponíveis. Uma interface Ethernet virtual não comprova acesso à camada 2 do laboratório nem capacidade wireless. `systemctl` pode falhar conforme a configuração; o inventário preserva outras seções. Wireless requer interface visível no Linux, driver compatível, modo monitor e canal original identificável. Rotas do Windows são manuais. Use diretório no filesystem Linux para arquivos de autenticação/artefatos quando precisar de permissões POSIX: mounts Windows podem não reproduzir `0600`/`0700` como esperado.

<a id="interface"></a>
## 3. Menu, IDs e cancelamento

```sh
python pyops.py
```

O menu agrupa Red, Blue, Purple e Misc, e exibe ID, aliases, tipo, estado e motivos de indisponibilidade. Um plugin com múltiplas táticas pode aparecer mais de uma vez. Digite o **ID ou alias**, não a posição visual. `000`, Ctrl+C ou EOF no prompt principal encerram o menu. Uma opção inválida mantém o prompt; ao terminar ou cancelar um plugin, o menu reaparece.

**`001` seleciona `tcp_scan`; `ops:001` seleciona `network_reference`.** `ops:901` e `ops:902` são aliases do mesmo scanner. Os IDs `043` e `080` conservam os zeros iniciais.

Nos plugins novos, a ajuda é seguida de `Argumentos (Ctrl+C cancela):`. Digite somente a linha de argumentos do plugin, com aspas quando necessário:

```text
ID ou alias (000 para sair): dns_records
Argumentos (Ctrl+C cancela): --domain example.test --types A MX
```

O texto é dividido com `shlex.split`, sem execução de shell: variáveis, glob e `~` não são expandidos automaticamente nessa linha. Não inclua `run`, o ID, `--format` ou `--output-dir`. As duas últimas opções pertencem exclusivamente à CLI `run`. O menu usa `outputs` e imprime JSON indentado. `--help` ou erro de parsing retorna ao menu. Ctrl+C/EOF cancela; durante execução dos plugins novos, o wrapper tenta finalizar o relatório.

Os antigos `043`, `080` e `tcp_rev_shell` conservam prompts próprios, descritos no catálogo. `run` para esses IDs termina com código 3, sem abrir sessão interativa. Cancelamento no menu não se traduz automaticamente em código 130 do processo: esse código pertence ao resultado da CLI `run`. SIGTERM é tratado como cancelamento durante a execução automatizada; SIGKILL, queda do host e interrupção durante a escrita final podem impedir limpeza e relatório.

<a id="cli"></a>
## 4. Referência da CLI

```text
pyops [-h] {list,info,run,doctor,matrix} ...
pyops list [--tactic ID] [--technique ID] [--group GRUPO] [--kind TIPO] [--available] [--format {text,json}]
pyops info PLUGIN
pyops run PLUGIN [ARGUMENTOS_DO_PLUGIN] [--format {text,json}] [--output-dir CAMINHO]
pyops doctor
pyops matrix [--format {markdown,json}]
```

`-h`/`--help` está disponível no parser principal, nos subcomandos e nos plugins automatizáveis. `pyops run ID --help` inclui as opções de saída adicionadas pela CLI. Sem subcomando, abre o menu. IDs desconhecidos e opções inválidas produzem erro de parser (2).

| Comando / opção | Tipo, padrão e comportamento |
|---|---|
| `list --tactic` | Texto opcional, correspondência exata com ID de tática, ex. `TA0043` |
| `list --technique` | Texto opcional, correspondência exata, ex. `T1590.002` |
| `list --group` | Texto opcional; grupos atuais `Red`, `Blue`, `Purple`, `Misc`; diferencia maiúsculas |
| `list --kind` | Texto opcional; valores atuais `tool`, `reference` |
| `list --available` | Flag, padrão falso; exclui entradas com `unavailable` global não vazio |
| `list --format` | `text` (padrão) ou `json`; texto resume entradas, JSON contém metadados completos |
| `info PLUGIN` | ID/alias obrigatório; imprime metadados JSON e, para automatizáveis, ajuda textual em seguida |
| `run PLUGIN` | ID/alias obrigatório; todos os argumentos seguintes são do parser do plugin acrescido das duas opções abaixo |
| `run ... --format` | `text` (padrão) ou `json`; **text também é JSON**, indentado; json usa uma linha |
| `run ... --output-dir` | Caminho, padrão `outputs`; raiz dos artefatos novos, não dos legados |
| `doctor` | Sem opções específicas; JSON de ambiente, erros do loader e metadados por plugin/operação |
| `matrix --format` | `markdown` (padrão) ou `json`; não aceita filtros de `list` |

Filtros de `list` são combinados por interseção. Valores de filtro inexistentes resultam em lista vazia, não erro. `--available` não testa privilégios, alvos ou todas as operações: uma entrada com pelo menos uma operação disponível pode passar no filtro.

`info` **não produz um documento JSON único** quando também imprime ajuda. Para processar metadados use `list --format json` ou `doctor`. `doctor` retorna 1 se houver erros de carregamento e 0 caso contrário, **mesmo com dependências ausentes**. Diagnósticos do loader vão para stderr. `matrix` mostra classificação do catálogo, não resultados de uma execução.

```sh
python pyops.py list --tactic TA0043 --group Red --kind tool --format json
python pyops.py list --technique T1083 --available
python pyops.py info ops:104
python pyops.py run dns_records --help
python pyops.py doctor > doctor.json
python pyops.py matrix --format markdown > matriz.md
python pyops.py matrix --format json > matriz.json
```

<a id="catalogo"></a>
## 5. Catálogo das 29 entradas

Cada tabela abaixo foi conferida com o parser correspondente. `—` em padrão significa sem valor padrão útil; não significa obrigatoriedade. Campos condicionais são detalhados após a tabela. Todos os plugins automatizáveis também aceitam `-h`/`--help`; somente via `run`, aceitam `--format` e `--output-dir` conforme a seção anterior.

Convenções compartilhadas:

- Inteiro positivo: mínimo 1; sem máximo no parser, salvo limite de execução explicitado. Tempos são segundos. Um timeout por consulta/comando não é prazo global de um lote.
- Domínio: normalização IDNA, minúsculas, ponto final removido, até 253 caracteres e rótulos de até 63; não aceita URL. Host: IP ou domínio. URL: HTTP/HTTPS, host válido, sem usuário/senha embutidos; redirecionamentos podem levar a outro host.
- Portas: lista separada por vírgulas e intervalos inclusivos, ex. `80,443,8000-8010`, entre 1 e 65535, deduplicada e ordenada.
- Arquivos de linhas: texto legível pelo ambiente, uma entrada por linha; somente os arquivos de nomes DNS/CNAME ignoram comentários `#`. Use UTF-8 e evite BOM. Caminhos devem existir quando usados; parsing de `Path` não comprova existência.
- Alvos de TCP/Nmap/PTR: IP, intervalo IP–IP inclusivo ou CIDR; TCP/Nmap também aceitam hostname. CIDR é normalizado e limitado a 4096 endereços totais, expandindo `hosts()`; intervalo admite até 4096 IPs da mesma versão. PTR exige IPs após expansão. Esses limites **não** se aplicam automaticamente à descoberta ARP.
- Salvo indicação contrária, não exige root: requer leitura das entradas, escrita na saída e conectividade apropriada. Falhas de dependências declaradas dão `unavailable`; falhas em execução podem ser `failed` ou `partial`. Cancelamento comum: Ctrl+C e relatório dos achados já obtidos, quando possível. Todos os novos plugins produzem `result.json`; artefatos adicionais são citados individualmente.
- `example.test`, `192.0.2.0/24`, `198.51.100.0/24`, MACs locais e `eth0`/`wlan0` são valores ilustrativos. Substitua pelos recursos do laboratório. Loopback pressupõe fixture local ativa quando houver serviço. WHOIS/CT, Google, SOCMINT e enriquecimento WHOIS contatam serviços externos mesmo com domínio de teste; seus exemplos não são testes offline.

- [dns_records — Registros DNS](#plugin-dns_records)
- [reverse_dns — DNS reverso](#plugin-reverse_dns)
- [cname_inventory — Inventário CNAME](#plugin-cname_inventory)
- [dns_zone_transfer — Transferência de zona DNS](#plugin-dns_zone_transfer)
- [domain_intelligence — WHOIS e certificados](#plugin-domain_intelligence)
- [http_headers — Cabeçalhos HTTP](#plugin-http_headers)
- [website_inventory — Inventário de site](#plugin-website_inventory)
- [search_queries — Consultas de reconhecimento](#plugin-search_queries)
- [document_metadata — Metadados de documentos](#plugin-document_metadata)
- [tcp_scan — Scanner TCP](#plugin-tcp_scan)
- [nmap_scan — Nmap](#plugin-nmap_scan)
- [arp_discovery — Descoberta ARP](#plugin-arp_discovery)
- [linux_inventory — Inventário Linux](#plugin-linux_inventory)
- [filesystem_audit — Auditoria de arquivos](#plugin-filesystem_audit)
- [local_exposure_audit — Exposição local (JALESC)](#plugin-local_exposure_audit)
- [smb_inventory — Inventário SMB](#plugin-smb_inventory)
- [arp_mitm_lab — ARP MITM de laboratório](#plugin-arp_mitm_lab)
- [wireless_lab — Wireless de laboratório](#plugin-wireless_lab)
- [wsl_vbox_routes — Rotas WSL/VirtualBox](#plugin-wsl_vbox_routes)
- [network_reference — Referência de rede Linux](#plugin-network_reference)
- [windows_reference — Referência Windows](#plugin-windows_reference)
- [find_reference — Referência find](#plugin-find_reference)
- [vim_reference — Referência Vim](#plugin-vim_reference)
- [root_recovery_reference — Recuperação administrativa de root](#plugin-root_recovery_reference)
- [restricted_shell_reference — Referência de shells restritos](#plugin-restricted_shell_reference)
- [legacy_arp_agent — Agente ARP legado — lacuna](#plugin-legacy_arp_agent)
- [043 — Personal Attack Surface Management (OwL's Eyes)](#plugin-043)
- [080 — Web Server](#plugin-080)
- [tcp_rev_shell — TCP Reverse Shell](#plugin-tcp_rev_shell)

<a id="plugin-dns_records"></a>
### 5.1. dns_records — Registros DNS

**ID:** `dns_records`. **Aliases:** `ops:104`. **Grupo:** Red. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0043 / T1590.002.

**Finalidade:** Consulta registros e nomes fornecidos pelo operador.

**Dependências declaradas:** python: `dns`. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--domain` | domínio | sim | `—` | convenções e condições abaixo |
| `--timeout` | inteiro positivo | não | `10` | >= 1 |
| `--types` | texto; um ou mais | não | `['A', 'AAAA', 'NS', 'MX', 'TXT', 'SOA']` | A, AAAA, NS, MX, TXT, SOA, CNAME |
| `--names-file` | caminho | não | `—` | convenções e condições abaixo |

Consulta o domínio base e, opcionalmente, os nomes adicionais, sem brute force implícito. `--names-file` aceita rótulos como `www` ou nomes terminados em `.example.test`; entradas diferentes recebem o sufixo do domínio. Evite repetir o domínio base no arquivo: nesse caso o código adiciona o sufixo novamente. Linhas vazias e comentários são ignorados; nomes são deduplicados.

```sh
# Mínimo: tipos padrão A, AAAA, NS, MX, TXT, SOA
python pyops.py run dns_records --domain example.test
# lab/nomes.txt: www em uma linha, api.example.test em outra
python pyops.py run dns_records --domain example.test --names-file lab/nomes.txt --types A CNAME --timeout 5
```

Achados: `name`, `type`, `status` (`answer`, `nxdomain`, `no_answer`) e `values`. NXDOMAIN/ausência de registro são achados, não falha do comando; timeout/SERVFAIL pode tornar o resultado parcial. Usa resolvers do sistema; não há opção pública para servidor DNS ou porta. Configure a fixture DNS no ambiente. Cancelamento pode aguardar a consulta corrente.

<a id="plugin-reverse_dns"></a>
### 5.2. reverse_dns — DNS reverso

**ID:** `reverse_dns`. **Aliases:** `ops:103`. **Grupo:** Red. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0043 / T1590.002.

**Finalidade:** Consulta PTR para IP, intervalo ou CIDR (até 4096 endereços).

**Dependências declaradas:** python: `dns`. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--target` | texto | sim | `—` | convenções e condições abaixo |
| `--timeout` | inteiro positivo | não | `10` | >= 1 |

Executa PTR sequencialmente. Apesar de `--target` ser texto no parser, hostname não é aceito na conversão final para IP. Não usa `--domain` nem arquivo de alvos.

```sh
python pyops.py run reverse_dns --target 192.0.2.10
python pyops.py run reverse_dns --target 192.0.2.10-192.0.2.12 --timeout 2
python pyops.py run reverse_dns --target 192.0.2.0/30
```

Achados acrescentam `ip` aos campos de consulta DNS. PTR não prova propriedade ou identidade do serviço. Redes excessivas/intervalos incompatíveis falham na execução; respostas ausentes não demonstram host desligado. Cancelamento preserva consultas concluídas.

<a id="plugin-cname_inventory"></a>
### 5.3. cname_inventory — Inventário CNAME

**ID:** `cname_inventory`. **Aliases:** `ops:202`. **Grupo:** Red. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0043 / T1590.002.

**Finalidade:** Inventaria aliases DNS; não confirma vulnerabilidade de takeover.

**Dependências declaradas:** python: `dns`. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--domain` | domínio | sim | `—` | convenções e condições abaixo |
| `--timeout` | inteiro positivo | não | `10` | >= 1 |
| `--names-file` | caminho | sim | `—` | convenções e condições abaixo |

`--names-file` é obrigatório: rótulos ou FQDNs, uma entrada por linha, comentários `#` e linhas vazias ignorados. O domínio base é aceito diretamente; nomes fora dele recebem seu sufixo. Não descobre nomes automaticamente.

```sh
python pyops.py run cname_inventory --domain example.test --names-file lab/nomes.txt
python pyops.py run cname_inventory --domain example.test --names-file lab/nomes.txt --timeout 5
```

Cada achado inclui CNAMEs, `resolution` (consultas A dos destinos) e `takeover_confirmed: false`. CNAME sem resolução **não confirma takeover**: exige investigação independente de DNS, provedor e configuração. Falhas de resolução podem impedir o achado daquele nome e gerar erro parcial. Ctrl+C interrompe o lote.

<a id="plugin-dns_zone_transfer"></a>
### 5.4. dns_zone_transfer — Transferência de zona DNS

**ID:** `dns_zone_transfer`. **Aliases:** `ops:201`. **Grupo:** Red. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0043 / T1590.002.

**Finalidade:** Consulta AXFR nos servidores autoritativos do domínio informado.

**Dependências declaradas:** python: `dns`. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--domain` | domínio | sim | `—` | convenções e condições abaixo |
| `--timeout` | inteiro positivo | não | `10` | >= 1 |

Descobre NS, resolve cada servidor por A e tenta AXFR no primeiro IPv4 encontrado. Não aceita servidor/porta explícitos e não usa IPv6 nessa seleção. Requer fixture autoritativa que permita transferência para o operador.

```sh
python pyops.py run dns_zone_transfer --domain example.test
python pyops.py run dns_zone_transfer --domain example.test --timeout 5
```

Sucesso por servidor: `server`, `status: transferred`, `records` em texto de zona. Ausência de NS aparece como achado DNS; recusa, timeout ou NS sem IPv4 entram em `errors`, normalmente `partial`. Transferência autorizada descreve exposição da zona ao cliente atual, não exploração automática. Ctrl+C cancela; não há arquivo de zona separado além dos registros em JSON.

<a id="plugin-domain_intelligence"></a>
### 5.5. domain_intelligence — WHOIS e certificados

**ID:** `domain_intelligence`. **Aliases:** `ops:102`. **Grupo:** Red. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0043 / T1596.002; TA0043 / T1596.003.

**Finalidade:** Consulta WHOIS e transparência de certificados, com fontes distintas.

**Dependências declaradas:** python: `requests`; executable: `whois`. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--domain` | domínio | um dos dois, exclusivo | `—` | convenções e condições abaixo |
| `--domains-file` | caminho | um dos dois, exclusivo | `—` | convenções e condições abaixo |
| `--timeout` | inteiro positivo | não | `20` | >= 1 |

Exige **exatamente um** entre `--domain` e `--domains-file`. Arquivo: domínio por linha, vazias ignoradas, sem comentários; deduplica nomes. Consulta `whois` e `https://crt.sh/` separadamente por domínio, sempre com as duas fontes. Não existe seleção de fonte nem modo offline.

```sh
# Exemplo de sintaxe; contata serviços externos
python pyops.py run domain_intelligence --domain example.test
python pyops.py run domain_intelligence --domains-file lab/dominios.txt --timeout 10
```

Achados WHOIS: `domain`, `source: whois`, `raw`; CT: `source: certificate_transparency`, `names` únicos ordenados. Pode preservar WHOIS mesmo com CT bloqueado e vice-versa. HTTP inválido, conteúdo não JSON, limites do serviço e backend indisponível são causas comuns. Certificados históricos não comprovam serviço ativo. Ctrl+C preserva o que já foi coletado.

<a id="plugin-http_headers"></a>
### 5.6. http_headers — Cabeçalhos HTTP

**ID:** `http_headers`. **Aliases:** `ops:903`. **Grupo:** Red. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0007 / T1046 (internal); TA0043 / T1595 (external).

**Finalidade:** Coleta cabeçalhos, status e redirecionamentos com TLS validado.

**Dependências declaradas:** python: `requests`. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--url` | URL HTTP(S) | sim | `—` | convenções e condições abaixo |
| `--context` | texto | sim | `—` | internal, external |
| `--timeout` | inteiro positivo | não | `15` | >= 1 |

Usa HEAD com redirecionamentos e validação TLS. Não faz fallback GET se o servidor recusar HEAD. Contexto é classificação declarada, não descoberta automática da topologia.

```sh
python pyops.py run http_headers --url http://127.0.0.1:8000/ --context internal
python pyops.py run http_headers --url https://web.example.test/ --context external --timeout 5
```

Achado: URL final, `status_code`, `headers`, cadeia `redirects`. HTTP >=400 gera achado e erro parcial. Certificado não confiável, DNS, proxy e timeout podem falhar antes de qualquer achado. Não há `--insecure`; configure confiança TLS do ambiente. Cabeçalho não é confirmação de versão ou vulnerabilidade. Ctrl+C encerra a coleta, sujeito à chamada corrente.

<a id="plugin-website_inventory"></a>
### 5.7. website_inventory — Inventário de site

**ID:** `website_inventory`. **Aliases:** `ops:106`. **Grupo:** Red. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0043 / T1594; TA0043 / T1590.002; TA0043 / T1596.002.

**Finalidade:** Extrai links de uma página e enriquece hosts selecionados com DNS/WHOIS.

**Dependências declaradas:** python: `requests`; python: `bs4`. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--url` | URL HTTP(S) | sim | `—` | convenções e condições abaixo |
| `--timeout` | inteiro positivo | não | `15` | >= 1 |
| `--enrich` | domínio; zero ou mais | não | `[]` | convenções e condições abaixo |

Baixa uma única página (até 10 MiB) e extrai `href`/`src` HTTP(S), resolvendo relativos pela URL final. Não rastreia recursivamente nem baixa os links. `--enrich` recebe zero ou mais hosts escolhidos pelo operador; só estes recebem A/WHOIS, mesmo que não tenham aparecido no HTML. Enriquecimento exige adicionalmente dnspython e `whois`, não declarados como dependências globais.

```sh
python pyops.py run website_inventory --url http://127.0.0.1:8000/
# WHOIS abaixo pode sair do laboratório
python pyops.py run website_inventory --url http://web.example.test/ --enrich web.example.test api.example.test --timeout 10
```

Achados de links: `url`, `host`, `source`; enriquecimentos acrescentam achados DNS e WHOIS. HTML sem links pode produzir sucesso vazio. Bloqueio HTTP, download excessivo ou dependências do enriquecimento geram falhas/resultado parcial. Não interpreta JavaScript. Ctrl+C permite relatório dos achados já emitidos.

<a id="plugin-search_queries"></a>
### 5.8. search_queries — Consultas de reconhecimento

**ID:** `search_queries`. **Aliases:** `ops:105`. **Grupo:** Red. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0043 / T1593.002.

**Finalidade:** Gera URLs de consultas; abre navegador somente com --open-browser.

**Dependências declaradas:** nenhuma dependência externa global declarada. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--query` | texto | sim | `—` | convenções e condições abaixo |
| `--site` | domínio; repetível | não | `[]` | convenções e condições abaixo |
| `--filetype` | texto; repetível | não | `[]` | pdf, doc, docx, xls, xlsx, ppt, pptx, txt, csv |
| `--open-browser` | flag | não | `False` | convenções e condições abaixo |

Gera a consulta original, uma consulta adicional por `--site` e outra por `--filetype`; não faz produto cartesiano site × extensão. As opções repetíveis devem ser repetidas com seu nome. Só `--open-browser` tenta abrir URLs; sem ele não há coleta ou consulta HTTP.

```sh
python pyops.py run search_queries --query 'inventario de laboratorio'
python pyops.py run search_queries --query 'inventario' --site example.test --site lab.example.test --filetype pdf --filetype csv
# Variante com navegador: envia as consultas ao mecanismo externo
python pyops.py run search_queries --query 'site:example.test laboratorio' --open-browser
```

Produz `queries.txt` e achados `query`, `url`, `status: query_generated`. URLs geradas não são resultados de pesquisa. Falha ao abrir navegador deixa resultado parcial; não há timeout configurável ou exportação de snippets. Ctrl+C cancela a geração/abertura.

<a id="plugin-document_metadata"></a>
### 5.9. document_metadata — Metadados de documentos

**ID:** `document_metadata`. **Aliases:** `ops:101`. **Grupo:** Red. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0043 / T1589; TA0043 / T1592.002.

**Finalidade:** Descobre/importa documentos, extrai metadados e exporta JSON/CSV.

**Dependências declaradas:** executable: `exiftool`; python: `requests`; python: `bs4`. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--files` | caminho; um ou mais | não | `[]` | convenções e condições abaixo |
| `--urls-file` | caminho | não | `—` | convenções e condições abaixo |
| `--url` | URL HTTP(S); repetível | não | `[]` | convenções e condições abaixo |
| `--domain` | domínio | não | `—` | convenções e condições abaixo |
| `--timeout` | inteiro positivo | não | `30` | >= 1 |
| `--max-documents` | inteiro positivo | não | `20` | >= 1 |

Combine entradas locais e remotas; pelo menos uma de `--files`, `--url`, `--urls-file`, `--domain` é exigida **na execução**. `--files` recebe vários caminhos; `--url` é repetível; `--urls-file` contém URL por linha, sem comentários. `--domain` consulta Google por PDF e tenta extrair links do domínio/subdomínios com extensões PDF/Office; não garante descoberta completa.

```sh
python pyops.py run document_metadata --files lab/fixture.pdf
python pyops.py run document_metadata --files lab/fixture.pdf lab/fixture.docx --max-documents 2
python pyops.py run document_metadata --url http://127.0.0.1:8000/fixture.pdf --urls-file lab/urls.txt --timeout 10
# Busca externa, opcional; pode retornar bloqueio ou vazio
python pyops.py run document_metadata --domain example.test --max-documents 5
```

Downloads limitados a 25 MiB cada, gravados como `document-N.bin`; ExifTool identifica conteúdo independentemente da extensão. `--max-documents` limita o conjunto processado (locais primeiro). Locais excedentes são truncados sem aviso específico; downloads interrompidos pelo limite registram erro. Caminhos locais repetidos não são deduplicados; URLs são.

Saídas: `metadata.csv` (`File,Field,Value`), `search-url.txt` se houve busca, documentos baixados e metadados completos nos achados `{file, metadata}`. O CSV seleciona Author, Creator, CreatorTool, Producer, Software, MIMEType, CreateDate e ModifyDate, quando presentes. Datas/autoria são pistas, não identidade comprovada. Mesmo uso local exige requests/bs4 e ExifTool declarados. Arquivo ausente, metadados inválidos, bloqueio HTTP/TLS e busca sem links geram erros parciais; prefira arquivos sintéticos/URLs próprios. Ctrl+C pode deixar downloads já gravados sem CSV final.

<a id="plugin-tcp_scan"></a>
### 5.10. tcp_scan — Scanner TCP

**ID:** `tcp_scan`. **Aliases:** `ops:901`, `ops:902`, `001`. **Grupo:** Red. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0007 / T1046 (internal); TA0043 / T1595 (external).

**Finalidade:** Conexões TCP com concorrência limitada e resultado por porta.

**Dependências declaradas:** nenhuma dependência externa global declarada. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--target` | texto | sim | `—` | convenções e condições abaixo |
| `--ports` | portas | sim | `—` | convenções e condições abaixo |
| `--context` | texto | sim | `—` | internal, external |
| `--timeout` | inteiro positivo | não | `3` | >= 1 |
| `--workers` | inteiro positivo | não | `16` | >= 1 |

Abre conexões TCP completas, sem identificação de serviço. Até 65536 pares host/porta e 128 workers, validados em execução; padrão 16 workers. Hosts são expandidos antes do agendamento; resultado não tem ordem garantida.

```sh
python pyops.py run tcp_scan --target 127.0.0.1 --ports 8000 --context internal
python pyops.py run ops:901 --target 192.0.2.0/30 --ports 80,443,8000-8002 --context external --workers 4 --timeout 1
python pyops.py run 001 --target 127.0.0.1 --ports 22,8000 --context internal
```

Achados: `host`, `port`, `status` (`open`, `closed`, `timeout`, `error`), e mensagem em caso de erro. `closed` e `timeout` não tornam o resultado parcial; `error` torna. Aberta significa conexão aceita naquele instante; timeout não comprova filtragem. Ctrl+C cancela tarefas pendentes e aguarda threads já ativas, normalmente até seus timeouts; resolução de nomes pode afetar o prazo.

<a id="plugin-nmap_scan"></a>
### 5.11. nmap_scan — Nmap

**ID:** `nmap_scan`. **Aliases:** `ops:908`. **Grupo:** Red. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0007 / T1046 (internal); TA0043 / T1595 (external).

**Finalidade:** Executa Nmap e preserva o XML original.

**Dependências declaradas:** executable: `nmap`. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--target` | texto | sim | `—` | convenções e condições abaixo |
| `--ports` | portas | sim | `—` | convenções e condições abaixo |
| `--context` | texto | sim | `—` | internal, external |
| `--timeout` | inteiro positivo | não | `300` | >= 1 |
| `--service-detection` | flag | não | `False` | convenções e condições abaixo |

Executa `nmap --unprivileged -sT -Pn -n` com portas explícitas, preservando `nmap.xml`. `--service-detection` adiciona `-sV`, com tráfego adicional de identificação. Timeout padrão 300 é do processo inteiro. Não aceita flags Nmap arbitrárias nem tem o limite de 65536 pares do scanner Python.

```sh
python pyops.py run nmap_scan --target 127.0.0.1 --ports 8000 --context internal
python pyops.py run nmap_scan --target 192.0.2.10 --ports 80,443 --context external --service-detection --timeout 60
```

Achados extraídos: host, porta, protocolo, `state`, atributos `service`, scripts de porta e resumo de hosts. XML é a fonte preservada; campos não extraídos continuam nele. Retorno não zero, timeout ou XML incompleto podem produzir erro; XML pode existir mesmo sem achados processados. Não requer root para o perfil configurado. Ctrl+C encerra o grupo de processos da operação.

<a id="plugin-arp_discovery"></a>
### 5.12. arp_discovery — Descoberta ARP

**ID:** `arp_discovery`. **Aliases:** `ops:909`. **Grupo:** Red. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0007 / T1018.

**Finalidade:** Descobre vizinhos com arp-scan em uma interface explícita.

**Dependências declaradas:** executable: `arp-scan`. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--interface` | texto | sim | `—` | convenções e condições abaixo |
| `--network` | texto | sim | `—` | convenções e condições abaixo |
| `--timeout` | inteiro positivo | não | `60` | >= 1 |

Requer interface local existente, mesma camada 2 dos vizinhos e privilégios/capacidades suficientes para `arp-scan` (normalmente root; não há prechecagem root no plugin). `--network` é IPv4 CIDR, normalizada em execução; não há limite de 4096 aplicado aqui. Escolha rede pequena de laboratório.

```sh
# Substitua eth0 e a rede pela interface e segmento isolado
python pyops.py run arp_discovery --interface eth0 --network 192.0.2.0/30
python pyops.py run arp_discovery --interface eth0 --network 192.0.2.0/30 --timeout 10
```

Salva `arp.txt`; interpreta linhas tabuladas em `ip`, `mac`, `vendor`. Emite consultas ARP, sem ativar forwarding, spoofing ou adicionar rotas. Sem restauração de configuração a fazer; Ctrl+C encerra o backend. Falta de capacidade, interface inexistente, rede inválida ou prazo excedido falham; saída vazia não comprova ausência de vizinhos.

<a id="plugin-linux_inventory"></a>
### 5.13. linux_inventory — Inventário Linux

**ID:** `linux_inventory`. **Aliases:** `ops:905`. **Grupo:** Red. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0007 / T1082.

**Finalidade:** Inventaria sistema, contas, rede, processos e serviços por seção.

**Dependências declaradas:** nenhuma dependência externa global declarada. Requisitos adicionais e privilégios estão descritos abaixo.

**Parâmetros próprios:** nenhum; ajuda e opções comuns de `run` continuam disponíveis.

Sem parâmetros próprios. Usa Linux `/proc`, `/etc`, contas locais e `ip`, `ss`, `ps`, `systemctl`, com timeout de 10 segundos por comando. Não exige root; visibilidade depende das permissões.

```sh
python pyops.py run linux_inventory
python pyops.py run linux_inventory --format json --output-dir relatorios
```

Achados por seção: sistema (kernel, arquitetura, hostname, UID/grupos e trechos de arquivos até 32768 caracteres), contas (nome, UID/GID, shell), interfaces, rotas, sockets, processos e serviços. Saídas de comandos ficam em `raw`, inclusive quando contêm JSON textual. Não há artefato especializado. Comando ausente ou serviço indisponível gera erro por seção e preserva outras. Dados refletem o namespace e privilégios atuais. Ctrl+C cancela a seção corrente.

<a id="plugin-filesystem_audit"></a>
### 5.14. filesystem_audit — Auditoria de arquivos

**ID:** `filesystem_audit`. **Aliases:** `ops:906`. **Grupo:** Purple. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0007 / T1083.

**Finalidade:** Inspeciona nomes, permissões e proprietários sem copiar conteúdo sensível.

**Dependências declaradas:** nenhuma dependência externa global declarada. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--roots` | caminho; um ou mais | sim | `—` | convenções e condições abaixo |
| `--max-entries` | inteiro positivo | não | `100000` | >= 1 |

Inspeciona metadados de entradas sob `--roots` (uma ou mais pastas), sem copiar conteúdo dos arquivos. Limite global padrão 100000 entradas; raízes sobrepostas podem repetir entradas. Exclui da descida `/proc`, `/sys`, `/dev`, `/run` quando encontrados como filhos, mas não confie nessa exclusão se informar essas pastas diretamente como raízes. Não segue links de diretórios; a raiz é resolvida antes da caminhada.

```sh
python pyops.py run filesystem_audit --roots lab
python pyops.py run filesystem_audit --roots lab/documentos lab/config --max-entries 500
```

Achados: caminho, modo, UID/GID, tamanho e indicadores `suid`, `sgid`, `world_writable`, `hidden`, `sensitive_filename`, `unknown_owner`, `unknown_group`, sempre `confirmed_vulnerability: false`. Nomes sensíveis reconhecidos: id_rsa, id_ed25519, credentials, shadow, .bash_history, .mysql_history, .dockercfg. Resumo `entries_inspected` é emitido se a caminhada terminar; atingir limite retorna antes dele. Permissões negadas, pasta inexistente e limite geram parcial. Não modifica os itens; Ctrl+C preserva indicadores já emitidos.

<a id="plugin-local_exposure_audit"></a>
### 5.15. local_exposure_audit — Exposição local (JALESC)

**ID:** `local_exposure_audit`. **Aliases:** `ops:602`. **Grupo:** Purple. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0007 / T1082; TA0007 / T1083.

**Finalidade:** Combina inventários e indicadores locais; não executa elevação de privilégios.

**Dependências declaradas:** nenhuma dependência externa global declarada. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--roots` | caminho; um ou mais | sim | `—` | convenções e condições abaixo |
| `--max-entries` | inteiro positivo | não | `100000` | >= 1 |

Combina o inventário Linux e a auditoria de arquivos com as mesmas regras de `--roots`/`--max-entries`. Acrescenta legibilidade/modo de `/etc/crontab` e `/etc/sudoers` e `getcap -r` nas raízes (30 segundos). Não executa elevação de privilégios, não lê conteúdo desses dois arquivos nessa etapa e não confirma vulnerabilidades.

```sh
python pyops.py run local_exposure_audit --roots lab
python pyops.py run local_exposure_audit --roots lab/config --max-entries 1000 --format json
```

Saída reúne seções e indicadores em `result.json`. Requer os executáveis de inventário e `getcap` para todas as seções, embora não declarados como dependências globais. Sem root obrigatório; acessos negados e ferramentas ausentes tornam o resultado parcial. Diferentemente da caminhada de auditoria, o comando getcap tem seu próprio comportamento recursivo. Ctrl+C interrompe a fase corrente; achados anteriores permanecem.

<a id="plugin-smb_inventory"></a>
### 5.16. smb_inventory — Inventário SMB

**ID:** `smb_inventory`. **Aliases:** `ops:904`. **Grupo:** Red. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0007 / T1046 (internal); TA0007 / T1135 (internal); TA0043 / T1595 (external); TA0043 / T1595.002 (external).

**Finalidade:** Enumera serviços e compartilhamentos; perfil de vulnerabilidades opcional.

**Dependências declaradas:** nenhuma dependência externa global declarada. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--target` | host | sim | `—` | convenções e condições abaixo |
| `--context` | texto | sim | `—` | internal, external |
| `--profile` | texto | não | `'shares'` | shares, services, rpc, vulnerabilities, all |
| `--auth-file` | caminho | não | `—` | convenções e condições abaixo |
| `--timeout` | inteiro positivo | não | `60` | >= 1 |

Um host por execução; não aceita CIDR, lista de portas ou comando remoto arbitrário. Sem root obrigatório, mas requer alcance a SMB e permissões no servidor. `--context` é obrigatório. Sem `--auth-file`, smbclient/rpcclient usam `-N` (sem senha solicitada).

| Perfil | Requisitos e operação | Artefatos adicionais |
|---|---|---|
| `shares` (padrão) | `smbclient -g -L //HOST`; lista compartilhamentos | `shares.txt` |
| `rpc` | `rpcclient -c 'srvinfo;netshareenumall'` | `rpc.txt` |
| `services` | Nmap TCP 139/445, scripts `smb-os-discovery,smb-protocols` | `services.xml`, `services.txt` |
| `vulnerabilities` | Nmap TCP 139/445, somente `smb-vuln-ms17-010` | `vulnerabilities.xml`, `vulnerabilities.txt` |
| `all` | Executa shares, services, rpc, nessa ordem; exige os três backends | Artefatos desses três perfis; **não inclui vulnerabilities** |

Arquivo Samba ilustrativo, com conta sintética a substituir (não versionar):

```ini
username = operador_lab
password = SENHA_SINTETICA_SUBSTITUIR
domain = LAB
```

```sh
chmod 600 lab/smb-auth.conf
python pyops.py run smb_inventory --target 127.0.0.1 --context internal
python pyops.py run smb_inventory --target 192.0.2.10 --context internal --profile rpc --auth-file lab/smb-auth.conf
python pyops.py run smb_inventory --target 192.0.2.10 --context internal --profile services
python pyops.py run smb_inventory --target 192.0.2.10 --context external --profile vulnerabilities --timeout 120
python pyops.py run smb_inventory --target 192.0.2.10 --context internal --profile all --auth-file lab/smb-auth.conf
```

A validação exige arquivo existente sem bits de acesso de grupo/outros; `0600` é o modo recomendado (não compara igualdade exata). Caminho é registrado em parâmetros, conteúdo não. Credenciais são usadas somente por smbclient/rpcclient; não são passadas aos scripts Nmap, ainda que o arquivo informado seja validado.

Achados por perfil: status, returncode, stdout; TXT reúne stdout/stderr; XML fornece portas, serviços e scripts de porta. Scripts no nível host podem estar só no XML. Resultado de script não substitui confirmação técnica independente. Em `external`, classificação do resultado é T1595.002 somente para perfil `vulnerabilities`; demais perfis usam T1595. Em `internal`, preserva T1046 e T1135. Falhas são isoladas por perfil; timeout vale para cada backend, não para o total de `all`. Ctrl+C encerra o processo corrente; arquivos incompletos podem permanecer.

<a id="plugin-arp_mitm_lab"></a>
### 5.17. arp_mitm_lab — ARP MITM de laboratório

**ID:** `arp_mitm_lab`. **Aliases:** `ops:801`. **Grupo:** Red. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0006 / T1557.002; TA0006 / T1040.

**Finalidade:** Sessão delimitada por interface, dois alvos e duração; restaura forwarding.

**Dependências declaradas:** executable: `arpspoof`; executable: `tcpdump`. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--interface` | texto | sim | `—` | convenções e condições abaixo |
| `--duration` | inteiro positivo | não | `30` | >= 1 |
| `--target` | IPv4 | sim | `—` | convenções e condições abaixo |
| `--gateway` | IPv4 | sim | `—` | convenções e condições abaixo |

Exige root, interface existente, alvo e gateway IPv4 **distintos**, mesma camada 2 e backends arpspoof/tcpdump. Duração de 1 a 3600 segundos; padrão 30. Não comprova automaticamente topologia, autorização ou capacidade da interface.

```sh
# Exemplo exclusivo de laboratório isolado; execute com privilégios apropriados
python pyops.py run arp_mitm_lab --interface eth0 --target 192.0.2.10 --gateway 192.0.2.1
python pyops.py run arp_mitm_lab --interface eth0 --target 192.0.2.10 --gateway 192.0.2.1 --duration 10
```

Grava `initial-state.json` com forwarding original e interface; escreve `1` em `/proc/sys/net/ipv4/ip_forward`; inicia tcpdump com filtro `host ALVO and host GATEWAY` e dois arpspoof em sentidos opostos. Esse filtro não captura necessariamente todo tráfego encaminhado do alvo para outros destinos. Salva `capture.pcap` e achado de operação/duração se concluir a espera.

Ao terminar, Ctrl+C, SIGTERM ou exceção, tenta encerrar somente seus processos e restaurar forwarding. `restored_forwarding` documenta restauração tentada com sucesso; erros de limpeza constam no relatório. Não há restauração explícita de caches ARP dos pares no código; comportamento de encerramento do backend não é garantia de recuperação completa. Confirme conectividade e tabelas ARP depois. SIGKILL/queda pode exigir restauração manual pelo `initial-state.json`. Backend que termina antes do prazo causa erro mesmo com código zero. Veja também o procedimento de laboratório.

<a id="plugin-wireless_lab"></a>
### 5.18. wireless_lab — Wireless de laboratório

**ID:** `wireless_lab`. **Aliases:** `ops:301`. **Grupo:** Red. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0006 / T1040; TA0006 / T1110.002.

**Finalidade:** Descoberta/captura, deauth delimitado ou análise offline, em operações separadas.

**Dependências declaradas:** nenhuma dependência externa global declarada. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--operation` | texto | sim | `—` | discover, capture, deauth, crack |
| `--interface` | texto | não | `—` | convenções e condições abaixo |
| `--bssid` | texto | não | `—` | convenções e condições abaixo |
| `--client` | texto | não | `—` | convenções e condições abaixo |
| `--channel` | inteiro positivo | não | `—` | >= 1 |
| `--duration` | inteiro positivo | não | `30` | >= 1 |
| `--count` | inteiro positivo | não | `5` | >= 1 |
| `--capture` | caminho | não | `—` | convenções e condições abaixo |
| `--wordlist` | caminho | não | `—` | convenções e condições abaixo |
| `--timeout` | inteiro positivo | não | `300` | >= 1 |

Operações são independentes; não há pipeline implícito descoberta → captura → deauth → crack. `discover`/`capture`/`deauth` exigem root, interface existente, driver compatível e canal original detectável por `iw dev INTERFACE info`. `crack` é offline e não exige root/interface.

| Operação | Parâmetros adicionais exigidos em execução | Tempo, efeito e saída |
|---|---|---|
| `discover` | `--interface` | airodump-ng por `--duration`; arquivos `wireless-*` PCAP/CSV |
| `capture` | `--interface`, `--bssid`, `--channel` | airodump-ng filtrado por BSSID/canal por `--duration`; `wireless-*` |
| `deauth` | `--interface`, `--bssid`, `--channel`, `--client` | aireplay-ng direcionado, `--count` repetições; prazo `--timeout`; `deauth.txt` |
| `crack` | `--capture`, `--wordlist`, ambos arquivos existentes | aircrack-ng com wordlist, prazo `--timeout`; `offline-analysis.txt` |

MACs devem ter seis octetos hexadecimais separados por `:`; validação é em execução. Canal é inteiro positivo sem máximo regulatório no parser; compatibilidade é decidida pelo backend/hardware. Nas operações online, `duration <= 3600` e `count <= 100` são validados mesmo quando o campo não controla aquela operação. `duration` não limita deauth; `count` não controla captura. Crack ignora os campos online. Wordlist: um candidato por linha, no formato aceito pelo aircrack-ng; captura deve ser compatível com esse backend.

```sh
# Interface e MACs ilustrativos: substituir pelos do laboratório isolado
python pyops.py run wireless_lab --operation discover --interface wlan0
python pyops.py run wireless_lab --operation discover --interface wlan0 --duration 10 --channel 6
python pyops.py run wireless_lab --operation capture --interface wlan0 --bssid 02:00:00:00:00:01 --channel 6 --duration 20
python pyops.py run wireless_lab --operation deauth --interface wlan0 --bssid 02:00:00:00:00:01 --client 02:00:00:00:00:02 --channel 6 --count 1 --timeout 10
python pyops.py run wireless_lab --operation crack --capture lab/fixture.cap --wordlist lab/candidatos.txt --timeout 30
```

Se a interface não estiver em modo monitor, cria interface temporária `owl` + oito caracteres e a ativa; se já estiver em monitor, usa a própria interface. Ajusta canal quando informado. Em `discover`, passar canal ajusta inicialmente a interface, mas o comando airodump não recebe `--channel`, portanto não garante captura fixa nesse canal.

Limpeza: encerra captura própria, remove apenas monitor criado pelo plugin, tenta restaurar canal original e registra artefatos existentes. Não gerencia NetworkManager, não executa `airmon-ng check kill` e não promete restaurar toda conectividade wireless. Canal ausente impede operação; falha de remoção/restauração gera erro parcial. Ctrl+C/SIGTERM passa pelo `finally`, mas SIGKILL/queda não. Deauth pode desconectar o cliente mesmo após término; confirme sua reconexão no laboratório.

`discover`/`capture` retornam T1040, `crack` T1110.002, `deauth` nenhuma relação ATT&CK no resultado atual. Achados online indicam operação/interface e canal restaurado; não interpretam handshake ou CSV. Crack guarda texto e returncode; código zero não é campo estruturado de senha encontrada. Ausência de handshake, wordlist inadequada, limites de hardware e término prematuro de captura precisam ser avaliados pelos artefatos.

<a id="plugin-wsl_vbox_routes"></a>
### 5.19. wsl_vbox_routes — Rotas WSL/VirtualBox

**ID:** `wsl_vbox_routes`. **Aliases:** `ops:003`. **Grupo:** Misc. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** sem relação estruturada.

**Finalidade:** Planeja, aplica e reverte rotas locais; Windows permanece manual.

**Dependências declaradas:** executable: `ip`. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--operation` | texto | não | `'plan'` | plan, apply, revert |
| `--interface` | texto | não | `—` | convenções e condições abaixo |
| `--gateway` | IPv4 | não | `—` | convenções e condições abaixo |
| `--network` | rede IPv4 estrita; repetível | não | `[]` | convenções e condições abaixo |
| `--state-file` | caminho | não | `—` | convenções e condições abaixo |

Usa `ip` e IPv4. Rede é `IPv4Network` estrita: informe endereço de rede, não endereço de host com máscara. `--network` é repetível. Interface deve existir até em `plan`; `apply`/`revert` exigem root. Não há prazo de sessão; comandos usam timeout interno padrão de 30 segundos.

| Operação | Requisitos condicionais | Efeito |
|---|---|---|
| `plan` (padrão) | interface, gateway, pelo menos uma network | Achados do plano e instrução Windows; não muda rotas/forwarding |
| `apply` | Mesmos campos, root, nenhuma rota existente com o mesmo destino | Ativa forwarding e adiciona rotas; conserva estado para reversão |
| `revert` | root e `--state-file` | Remove rotas que ainda correspondam exatamente a destino/gateway/interface e restaura forwarding conforme estado |

```sh
# Valores de exemplo; escolha interface/gateway alcançável reais antes de usar
python pyops.py run wsl_vbox_routes --interface eth0 --gateway 192.0.2.1 --network 198.51.100.0/24
python pyops.py run wsl_vbox_routes --operation plan --interface eth0 --gateway 192.0.2.1 --network 198.51.100.0/24 --network 203.0.113.0/24
# Alteração persistente até revert; requer root
python pyops.py run wsl_vbox_routes --operation apply --interface eth0 --gateway 192.0.2.1 --network 198.51.100.0/24
# Substitua pelo caminho revert_state retornado por apply
python pyops.py run wsl_vbox_routes --operation revert --state-file outputs/wsl_vbox_routes/ID_DA_EXECUCAO/route-state.json
```

`apply` consulta `ip -json route show`, recusa destinos já presentes e grava `route-state.json` antes da alteração, atualizando-o após cada rota adicionada. Após sucesso **não reverte automaticamente**. Falha/cancelamento dentro do bloco de aplicação chama restauração; erro durante essa restauração ainda pode deixar estado pendente. Não presume gateway Windows: instrução apenas recomenda `route print` e configuração manual do lado Windows.

Estado ilustrativo (não reutilize como estado real):

```json
{"forwarding":"0","routes":[{"network":"198.51.100.0/24","gateway":"192.0.2.1","interface":"eth0"}]}
```

Use somente estado produzido e revisado para a sessão. `revert` valida redes, gateways, interfaces e forwarding (`"0"`/`"1"`). Remove correspondências em ordem inversa; ignora rotas que já não correspondem. Só reescreve forwarding se o valor atual for `1`. A mensagem `restored` não dispensa leitura de `errors` nem verificação de rotas. Concorrência com outras mudanças de rede não é protegida; planeje uma operação por vez. Ctrl+C/queda após `apply` bem-sucedido não desfaz as rotas: execute `revert`.

<a id="plugin-network_reference"></a>
### 5.20. network_reference — Referência de rede Linux

**ID:** `network_reference`. **Aliases:** `ops:001`. **Grupo:** Misc. **Tipo/estado:** `reference` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** sem relação estruturada.

**Finalidade:** Comandos de consulta de interfaces, sockets, rotas e DNS.

**Dependências declaradas:** nenhuma dependência externa global declarada. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--search` | texto | não | `''` | convenções e condições abaixo |

Referência consultável de interfaces, conexões/sockets, rotas/vizinhos e DNS. Não requer os programas citados no texto nem privilégios especiais: não executa as instruções. `--search` faz busca de substring sem diferenciar maiúsculas no título e no conteúdo; vazio mostra todas as seções.

```sh
python pyops.py run network_reference
python pyops.py run network_reference --search 'rotas'
```

Achados: `section`, `text`, `executable: false`; somente `result.json`. Nenhuma correspondência produz sucesso com lista vazia. Erros típicos são argumento inválido ou saída sem permissão. Ctrl+C cancela como nos demais plugins novos. O guia não verifica aplicabilidade dos comandos ao host nem certifica cobertura ATT&CK.

<a id="plugin-windows_reference"></a>
### 5.21. windows_reference — Referência Windows

**ID:** `windows_reference`. **Aliases:** `ops:002`. **Grupo:** Misc. **Tipo/estado:** `reference` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** sem relação estruturada.

**Finalidade:** Referência Windows consultável sem executar comandos Windows.

**Dependências declaradas:** nenhuma dependência externa global declarada. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--search` | texto | não | `''` | convenções e condições abaixo |

Referência consultável de sistema, arquivos, processos, rede, contas e Registro do Windows. Não requer os programas citados no texto nem privilégios especiais: não executa as instruções. `--search` faz busca de substring sem diferenciar maiúsculas no título e no conteúdo; vazio mostra todas as seções.

```sh
python pyops.py run windows_reference
python pyops.py run windows_reference --search 'rede'
```

Achados: `section`, `text`, `executable: false`; somente `result.json`. Nenhuma correspondência produz sucesso com lista vazia. Erros típicos são argumento inválido ou saída sem permissão. Ctrl+C cancela como nos demais plugins novos. O guia não verifica aplicabilidade dos comandos ao host nem certifica cobertura ATT&CK.

<a id="plugin-find_reference"></a>
### 5.22. find_reference — Referência find

**ID:** `find_reference`. **Aliases:** `ops:907`. **Grupo:** Misc. **Tipo/estado:** `reference` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** TA0007 / T1083.

**Finalidade:** Exemplos de busca por nome, tipo, tamanho e permissões.

**Dependências declaradas:** nenhuma dependência externa global declarada. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--search` | texto | não | `''` | convenções e condições abaixo |

Referência consultável de nomes, profundidade, permissões, tamanho e data em find. Não requer os programas citados no texto nem privilégios especiais: não executa as instruções. `--search` faz busca de substring sem diferenciar maiúsculas no título e no conteúdo; vazio mostra todas as seções.

```sh
python pyops.py run find_reference
python pyops.py run find_reference --search 'permissões'
```

Achados: `section`, `text`, `executable: false`; somente `result.json`. Nenhuma correspondência produz sucesso com lista vazia. Erros típicos são argumento inválido ou saída sem permissão. Ctrl+C cancela como nos demais plugins novos. O guia não verifica aplicabilidade dos comandos ao host nem certifica cobertura ATT&CK.

<a id="plugin-vim_reference"></a>
### 5.23. vim_reference — Referência Vim

**ID:** `vim_reference`. **Aliases:** `ops:603`. **Grupo:** Misc. **Tipo/estado:** `reference` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** sem relação estruturada.

**Finalidade:** Comandos de edição, navegação, pesquisa e saída do Vim.

**Dependências declaradas:** nenhuma dependência externa global declarada. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--search` | texto | não | `''` | convenções e condições abaixo |

Referência consultável de edição, navegação, salvar/sair e histórico no Vim. Não requer os programas citados no texto nem privilégios especiais: não executa as instruções. `--search` faz busca de substring sem diferenciar maiúsculas no título e no conteúdo; vazio mostra todas as seções.

```sh
python pyops.py run vim_reference
python pyops.py run vim_reference --search 'salvar'
```

Achados: `section`, `text`, `executable: false`; somente `result.json`. Nenhuma correspondência produz sucesso com lista vazia. Erros típicos são argumento inválido ou saída sem permissão. Ctrl+C cancela como nos demais plugins novos. O guia não verifica aplicabilidade dos comandos ao host nem certifica cobertura ATT&CK.

<a id="plugin-root_recovery_reference"></a>
### 5.24. root_recovery_reference — Recuperação administrativa de root

**ID:** `root_recovery_reference`. **Aliases:** `ops:601`. **Grupo:** Misc. **Tipo/estado:** `reference` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** sem relação estruturada.

**Finalidade:** Guia de recuperação local; não altera boot, contas ou senhas.

**Dependências declaradas:** nenhuma dependência externa global declarada. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--search` | texto | não | `''` | convenções e condições abaixo |

Referência consultável de preparação com console/snapshot, recuperação administrativa e finalização do boot. Não requer os programas citados no texto nem privilégios especiais: não executa as instruções. `--search` faz busca de substring sem diferenciar maiúsculas no título e no conteúdo; vazio mostra todas as seções.

```sh
python pyops.py run root_recovery_reference
python pyops.py run root_recovery_reference --search 'preparação'
```

Achados: `section`, `text`, `executable: false`; somente `result.json`. Nenhuma correspondência produz sucesso com lista vazia. Erros típicos são argumento inválido ou saída sem permissão. Ctrl+C cancela como nos demais plugins novos. O guia não verifica aplicabilidade dos comandos ao host nem certifica cobertura ATT&CK.

<a id="plugin-restricted_shell_reference"></a>
### 5.25. restricted_shell_reference — Referência de shells restritos

**ID:** `restricted_shell_reference`. **Aliases:** `ops:604`. **Grupo:** Misc. **Tipo/estado:** `reference` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** sem relação estruturada.

**Finalidade:** Consulta de limitações e superfícies de escape em ambientes de laboratório.

**Dependências declaradas:** nenhuma dependência externa global declarada. Requisitos adicionais e privilégios estão descritos abaixo.

| Parâmetro | Tipo / quantidade | Obrigatório no parser | Padrão | Alternativas / limites do parser |
|---|---|---|---|---|
| `--search` | texto | não | `''` | convenções e condições abaixo |

Referência consultável de inventário de comandos permitidos, editores, interpretadores e controles de isolamento. Não requer os programas citados no texto nem privilégios especiais: não executa as instruções. `--search` faz busca de substring sem diferenciar maiúsculas no título e no conteúdo; vazio mostra todas as seções.

```sh
python pyops.py run restricted_shell_reference
python pyops.py run restricted_shell_reference --search 'controles'
```

Achados: `section`, `text`, `executable: false`; somente `result.json`. Nenhuma correspondência produz sucesso com lista vazia. Erros típicos são argumento inválido ou saída sem permissão. Ctrl+C cancela como nos demais plugins novos. O guia não verifica aplicabilidade dos comandos ao host nem certifica cobertura ATT&CK.

<a id="plugin-legacy_arp_agent"></a>
### 5.26. legacy_arp_agent — Agente ARP legado — lacuna

**ID:** `legacy_arp_agent`. **Aliases:** `ops:1001`. **Grupo:** Misc. **Tipo/estado:** `tool` / `experimental`. **Interface:** CLI `run` e menu. **ATT&CK do catálogo:** sem relação estruturada.

**Finalidade:** Registro da opção sem implementação original funcional.

**Dependências declaradas:** nenhuma dependência externa global declarada. Requisitos adicionais e privilégios estão descritos abaixo.

**Parâmetros próprios:** nenhum; ajuda e opções comuns de `run` continuam disponíveis.

Registro de lacuna, sem parâmetros próprios nem requisitos que possam habilitá-lo. `automated` é verdadeiro porque existe `execute`, mas o wrapper detecta a indisponibilidade antes de executá-lo.

```sh
python pyops.py info legacy_arp_agent
# Retorna unavailable (3); não cria agente nem inicia ARP
python pyops.py run legacy_arp_agent
```

Retorna `errors` com “Implementação original ausente; backlog fora da portabilidade.” e tenta gravar `result.json`. Não há alvos, duração ou mecanismo de restauração. Não confundir com `arp_discovery` ou `arp_mitm_lab`; instalar dependências não preenche esta lacuna.

<a id="plugin-043"></a>
### 5.27. 043 — Personal Attack Surface Management (OwL's Eyes)

**ID:** `043`. **Aliases:** nenhum. **Grupo:** Purple. **Tipo/estado:** `tool` / `experimental`. **Interface:** somente menu. **ATT&CK do catálogo:** sem relação estruturada.

**Finalidade:** Ferramenta de reconhecimento e inteligência baseada no MITRE ATT&CK e OSINT.

**Dependências declaradas:** nenhuma dependência externa global declarada. Requisitos adicionais e privilégios estão descritos abaixo.

OwL's Eyes é somente interativo, sem aliases e sem mapeamentos ATT&CK estruturados em `ATTACK`, embora o hub declare tática TA0043. Não possui parâmetros de `run` nem contrato único de saída. Não exige root.

Sequência real: escolha `043` no menu principal; no hub, `1` OPSEC, `2` SOCMINT, `3` Footprint, `4` Breach, `5` Monitoring, `6` Social Engineering, `7` Defensive, `0` ou vazio volta. Somente **2 e 3** têm operação; 1/4/5/6/7 mostram aviso. Ctrl+C no hub volta ao menu principal.

| Prompt / escolha | Tipo, obrigatoriedade, padrão e limites |
|---|---|
| `OwL's Eyes >` | Escolha textual 0–7; vazio retorna |
| Módulo 2: Instagram | Username ou URL; opcional, vazio omite plataforma |
| Módulo 2: LinkedIn | Slug, texto de consulta ou URL `/in/`; opcional; ambos vazios cancelam |
| `Selecione o modo IG [1/2]` | Só se Instagram preenchido; 1 rápida, 2 completa; vazio/inválido vira 1 |
| `Pressione Enter para voltar...` | Ao fim do módulo 2 ou se dependências faltarem |
| `Footprint >` | 1 DNS, 2 WHOIS/CT, 0 ou vazio volta; depois linha de argumentos do plugin novo |

Exemplo mínimo sem coleta: `043` → `0`. Exemplo sintético de sequência SOCMINT (não executar sem alvo autorizado): `043` → `2` → Instagram `perfil_sintetico_lab` → LinkedIn vazio → modo `1` → Enter. Variante: Instagram vazio → slug LinkedIn sintético; não aparece prompt de modo IG. Variante Footprint: `043` → `3` → `1` → `--domain example.test --types A`; opção `2` recebe os argumentos de `domain_intelligence`.

Módulo 2 exige instaloader, requests e bs4 simultaneamente. Instagram tenta metadados de perfil; perfis privados não têm posts visíveis coletados. Modos 1/2 guardam até dez posts com shortcode, data, trecho de legenda (200 caracteres mais reticências) e URL; apesar do rótulo “fotos”, não há download de imagens. Modo 2 retém até 100 nomes por lista de seguidores/seguidos, mas as compreensões **continuam percorrendo o iterador**, portanto 100 não limita solicitações nem duração. O código não oferece prompt de login ou carrega explicitamente sessão autenticada; mensagens sugerindo login não comprovam suporte implementado.

Falhas Instagram acionam fallback com URLs de visualizadores e tentativa HTTP ao Dumpoir (10 s). Não é confirmação de existência, acesso ou confiabilidade do perfil. LinkedIn usa pesquisa Google e interpreta snippets HTML, sem timeout explícito; pode bloquear ou retornar vazio. Não há duração total nem cancelamento externo estruturado; use Ctrl+C. O módulo captura a interrupção, mas pode não salvar resultados acumulados.

Saída SOCMINT: `target_<alvo>_<timestamp>_socmint.json` no **diretório corrente**, JSON com chaves instagram/linkedin, sem envelope `Result`, sem `--output-dir` e sem garantia das permissões privadas do wrapper novo. Campos parciais e mensagens de bloqueio não provam ausência de exposição. Footprint delega aos plugins novos e usa seus resultados/`outputs`. Não inclua dossiês reais em commits.

<a id="plugin-080"></a>
### 5.28. 080 — Web Server

**ID:** `080`. **Aliases:** nenhum. **Grupo:** Misc. **Tipo/estado:** `tool` / `experimental`. **Interface:** somente menu. **ATT&CK do catálogo:** sem relação estruturada.

**Finalidade:** Usa um servidor web embutido para servir arquivos estáticos.

**Dependências declaradas:** executable: `ip`. Requisitos adicionais e privilégios estão descritos abaixo.

Servidor estático legado, somente menu, sem aliases ou ATT&CK estruturado. Requer `ip` para enumerar IPv4 e biblioteca padrão Python. Permissão para bind na porta e leitura da pasta; portas privilegiadas podem exigir capacidade/root conforme o host.

| Ordem / prompt | Tipo, obrigatoriedade, padrão e limites |
|---|---|
| `Escolha o número da interface` | Inteiro de uma lista de pares interface/IPv4; sem padrão; `0` cancela |
| `Digite a porta ... ou 0 para cancelar` | Inteiro 1–65535; sem padrão; `0` cancela |
| `Diretório a publicar (obrigatório)` | Pasta existente, `~` expandido; vazio/inválido encerra configuração |

Exemplo mínimo: menu `080` → escolha a linha de `lo - 127.0.0.1` (índice varia) → `8000` → `lab/publico`. Variante: escolha IPv4 da interface de laboratório e porta `8080`, com pasta sintética própria. Para apenas sair da configuração, use `0` na lista de interfaces.

Serve a pasta explicitamente indicada via `SimpleHTTPRequestHandler`; não altera diretório corrente. Pode listar diretórios e seguir links conforme o handler: publique apenas conteúdo preparado. Não tem autenticação, TLS ou timeout de sessão. Permanece até Ctrl+C; fecha o servidor e volta ao menu. Bind ocupado, interface sem IPv4, `ip` ausente, porta inválida e pasta sem acesso são falhas comuns.

Não produz `result.json`, não grava artefatos operacionais e não aceita `--output-dir`; mensagens e logs HTTP aparecem no terminal. “Servidor disponível” é mensagem antes da tentativa de bind, portanto confira erros subsequentes. `run 080` retorna 3.

<a id="plugin-tcp_rev_shell"></a>
### 5.29. tcp_rev_shell — TCP Reverse Shell

**ID:** `tcp_rev_shell`. **Aliases:** nenhum. **Grupo:** Red. **Tipo/estado:** `tool` / `experimental`. **Interface:** somente menu. **ATT&CK do catálogo:** sem relação estruturada.

**Finalidade:** Starts a TCP listener to accept incoming reverse shell connections or generates a client payload.

**Dependências declaradas:** nenhuma dependência externa global declarada. Requisitos adicionais e privilégios estão descritos abaixo.

Plugin legado somente interativo; sem aliases, dependências externas ou relação ATT&CK estruturada. A categoria textual “Command and Control” não preenche `ATTACK`. Requer socket IPv4 e permissões de bind/escrita conforme a opção. Use somente VM/loopback sob controle do operador: o cliente executa comandos com os privilégios do processo, sem autenticação ou criptografia.

| Ordem / prompt | Tipo, obrigatoriedade, padrão e limites |
|---|---|
| `Select an option` | 1 listener, 2 gerar cliente, 0 voltar; sem padrão |
| `Listening IP [0.0.0.0]` | Texto, vazio usa todas as interfaces IPv4; prefira 127.0.0.1 no laboratório local |
| `Listening Port [4444]` | Inteiro, vazio usa 4444; faixa efetiva depende do socket (0 pode escolher porta efêmera), não há validação 1–65535 própria |
| `RevShell@IP>` | Comando textual não vazio; `exit` ou `quit` envia saída e fecha sessão |
| `LHOST (Attacker IP)` | Texto não vazio, sem validação de host; usado literalmente no código gerado |
| `LPORT (Attacker Port)` | Texto não vazio, sem validação numérica na geração; deve representar porta válida ao executar cliente |

Exemplo de listener: menu `tcp_rev_shell` → `1` → `127.0.0.1` → `4444`; aguarda uma conexão. Ctrl+C encerra espera/sessão e fecha sockets. Exemplo de geração local: menu `tcp_rev_shell` → `2` → `127.0.0.1` → `4444`; gera `revshell_client.py` no diretório corrente, **sobrescrevendo arquivo homônimo**. Gerar não executa nem transfere o cliente. Exemplo mínimo para retornar: escolha `0`.

O cliente gerado requer Python, conecta ao endereço fornecido, trata `cd` localmente e executa demais comandos com `shell=True`. Não cole texto arbitrário nos campos LHOST/LPORT: são interpolados em código, sem escape. Listener lê até 4096 bytes por resposta; cliente lê até 1024 bytes por comando, sem protocolo de enquadramento, prazo ou reconexão. Saídas longas podem truncar/desalinhar e desconexão não é tratada de forma robusta. Não pressupõe sessão persistente confiável.

Porta ocupada, IP não local, entrada inválida e firewall impedem conexão. Não há relatório padronizado nem permissões privadas garantidas para o arquivo gerado. O cancelamento do listener fecha seus sockets, mas não desfaz comandos executados no cliente. Restaure a VM/arquivos de laboratório conforme os efeitos reais da sessão.

<a id="fluxos"></a>
## 6. Fluxos operacionais

Prepare uma pasta `lab` com fixtures sintéticas e registre escopo, interfaces e serviços esperados antes de executar. Estes fluxos são receitas para o operador, não evidência de execução durante a redação. Não use sucesso vazio como prova de ausência de exposição; correlacione resultados, erros, cobertura e fontes.

### Reconhecimento de domínio

Configure um DNS de laboratório no resolver do sistema para `example.test`; prepare `lab/nomes.txt` com `www` e `api`, um por linha. Confirme a autorização separada para fontes externas se usar WHOIS/CT.

```sh
python pyops.py run dns_records --domain example.test --types A AAAA MX NS --names-file lab/nomes.txt
python pyops.py run cname_inventory --domain example.test --names-file lab/nomes.txt
python pyops.py run reverse_dns --target 192.0.2.10-192.0.2.12
# Apenas se AXFR fizer parte do escopo do servidor autoritativo
python pyops.py run dns_zone_transfer --domain example.test
# Opcional: WHOIS e crt.sh são fontes externas, mesmo com example.test
python pyops.py run domain_intelligence --domain example.test
```

Leia tipos e estados por nome, compare PTR com resolução direta, separe dados históricos de CT de endpoints ativos. AXFR recusado não equivale a DNS inacessível; CNAME sem A é pista a revisar, nunca confirmação de takeover. Não há encadeamento automático entre esses resultados.

### Inventário web

Publique HTML sintético pelo `080` em loopback/8000, contendo links relativos e absolutos controlados. Prepare certificado confiável se usar HTTPS. Revise redirecionamentos e hosts antes de qualquer etapa posterior.

```sh
python pyops.py run http_headers --url http://127.0.0.1:8000/ --context internal
python pyops.py run website_inventory --url http://127.0.0.1:8000/
python pyops.py run search_queries --query 'inventario laboratorio' --site example.test --filetype pdf
```

Compare URL final, status HTTP, cadeia de redirecionamento e links. HEAD pode ser bloqueado enquanto GET funciona. `search_queries` sem navegador só gera URLs; não produz achados de páginas. Enriquecimento é opt-in por host e pode envolver WHOIS externo.

### Metadados

Crie documentos sintéticos ou copie fixtures aprovadas para `lab`; não publique documentos pessoais só para testar. Para arquivo de URLs, use uma URL de fixture por linha.

```sh
python pyops.py run document_metadata --files lab/fixture.pdf --max-documents 1
python pyops.py run document_metadata --urls-file lab/urls.txt --max-documents 3
```

Revise `metadata.csv` e os metadados completos em JSON. Compare campos esperados da fixture; campos ausentes não significam sanitização completa. Verifique se o limite cortou documentos e se downloads falharam. Busca por domínio é alternativa sujeita a bloqueios, não requisito do fluxo local.

### Descoberta de serviços

Prepare um serviço local conhecido, por exemplo o `080` em 127.0.0.1:8000, e escolha portas de teste explícitas. Não infira escopo a partir da rede atual.

```sh
python pyops.py run tcp_scan --target 127.0.0.1 --ports 8000,8001 --context internal --timeout 1
python pyops.py run nmap_scan --target 127.0.0.1 --ports 8000 --context internal --service-detection
```

Compare conexão aceita/recusada com Nmap e com a configuração do serviço. Detecção de versão pode ser aproximada. Para descoberta ARP, mude para segmento de laboratório com camada 2 e privilégios apropriados; loopback não substitui esse teste.

### Auditoria local

Prepare uma árvore sintética pequena e conhecida; comece com usuário normal para conhecer a visibilidade real. Não use `/` como primeiro teste.

```sh
python pyops.py run linux_inventory
python pyops.py run filesystem_audit --roots lab --max-entries 1000
python pyops.py run local_exposure_audit --roots lab --max-entries 1000
```

Leia `errors` por seção, verifique o resumo e compare indicadores com permissões reais. SUID, arquivo oculto ou nome sensível não prova vulnerabilidade. Não conclua que o host foi auditado integralmente se raiz, limite ou permissões restringiram a coleta.

### Enumeração SMB

Prepare um servidor SMB de laboratório e uma conta com permissões definidas. Use arquivo privado somente se necessário; os exemplos abaixo pressupõem serviço configurado em loopback.

```sh
python pyops.py run smb_inventory --target 127.0.0.1 --context internal --profile shares
python pyops.py run smb_inventory --target 127.0.0.1 --context internal --profile services
python pyops.py run smb_inventory --target 127.0.0.1 --context internal --profile rpc --auth-file lab/smb-auth.conf
```

Compare TXT, XML, retorno dos backends e permissões esperadas. Acesso negado não prova ausência de compartilhamentos. `all` reúne esses três perfis; o teste `vulnerabilities` é separado e deve ter escopo explícito. Nenhum perfil abre shell SMB interativo.

<a id="laboratorio"></a>
## 7. Preparação e restauração do laboratório

As receitas de ARP/MITM/wireless/rotas no catálogo documentam operações que alteram o ambiente. Execute somente em rede isolada e autorizada, com console de recuperação disponível. Não há prompt adicional de confirmação na CLI. Use o Python do ambiente virtual com os privilégios necessários; sob elevação, preserve explicitamente o caminho desse interpretador para não perder dependências. Arquivos gerados por root podem exigir esse usuário para leitura posterior.

Antes da sessão, registre `ip -br address`, `ip route show`, valor de `/proc/sys/net/ipv4/ip_forward` e, se wireless, `iw dev`/`iw dev INTERFACE info`. Confirme a relação entre alvo, gateway e interface. Prepare snapshot/console da VM; para wireless, anote canal e interfaces preexistentes. Nenhuma opção do PyOpS escolhe automaticamente a rede autorizada.

| Operação | Duração / interrupção | Estado e verificação posterior |
|---|---|---|
| Descoberta ARP | Timeout do backend (60 s padrão); Ctrl+C | Não altera rotas/forwarding; revise `arp.txt` e erros de capacidade |
| ARP MITM | 30 s padrão, até 3600; Ctrl+C/SIGTERM | Confira processos próprios encerrados, forwarding igual a `initial-state.json`, conectividade dos pares e caches ARP |
| Wireless discover/capture | 30 s padrão, até 3600; Ctrl+C/SIGTERM | Confira interface `owl...` removida quando criada, canal original restaurado e conectividade |
| Wireless deauth | Count 5 padrão, até 100; timeout 300 s padrão | Confira reconexão do cliente e restauração de interface/canal; `duration` não controla esse backend |
| Wireless crack | Timeout 300 s padrão; Ctrl+C | Sem configuração de rede alterada; preserve captura original e revise texto offline |
| Rotas plan | Retorno imediato após validação/relatório | Nenhuma alteração de rede; o plano não testa alcance do gateway |
| Rotas apply | Sem duração de sessão; rotas permanecem | Guarde `route-state.json`/`revert_state`; confira tabela e forwarding |
| Rotas revert | Uma execução de restauração | Compare tabela antes/depois e `errors`; não altera o lado Windows |

`Process` inicia subprocessos em grupos próprios, envia SIGTERM e pode usar SIGKILL após cerca de três segundos para encerrá-los. Não mata processos por nome. Mesmo assim, limpeza da operação pode falhar por permissões, dispositivo removido ou host interrompido. Não use SIGKILL como interrupção normal se depender do `finally`.

Se MITM não restaurar forwarding, compare o valor atual com `initial-state.json` e restaure manualmente o valor original usando o mecanismo administrativo do host; não suponha que era zero. Verifique se outra operação legítima depende de forwarding antes de alterar. O PyOpS não fornece um subcomando de recuperação MITM nem restauração explícita dos caches ARP.

Se wireless deixar uma interface temporária, identifique-a pelos dados da sessão/`iw dev` e remova somente a interface que a operação criou; restaure o canal registrado. Não apague uma interface monitor preexistente. Se não houver estado suficiente, recupere pelo console/snapshot do laboratório.

Para rotas, execute `revert` com o estado original, depois examine `ip route show` e forwarding. Destinos/gateways/interfaces divergentes não são removidos. Não substitua o arquivo de estado por um modelo do manual: ele representa o que foi efetivamente adicionado. Mudanças simultâneas no sistema e falhas entre adicionar uma rota e gravar seu estado podem exigir reconciliação manual. Configuração Windows/VirtualBox permanece responsabilidade do operador.

<a id="resultados"></a>
## 8. Resultados e automação

Plugins novos gravam, por padrão, esta árvore relativa ao diretório corrente:

```text
outputs/
  plugin_id/
    run_id/                 # UUID hexadecimal, sem hífens
      result.json
      ... artefatos especializados ...
```

`--output-dir` troca a raiz somente em `run`. Diretórios novos são criados solicitando `0700`; artefatos são finalizados com `0600` quando o filesystem permite. Diretórios preexistentes e ancestrais não são automaticamente endurecidos, e permissões durante escrita por backend podem depender dele/umask. Verifique armazenamento, ownership e acesso no WSL/mounts Windows.

Não há rotação, retenção automática ou remoção de dados preexistentes. Artefatos podem conter nomes, metadados, inventário local, capturas e informações de autenticação retornadas por backends. Mantenha-os fora de commits e trate-os conforme o escopo do laboratório. Os plugins antigos têm caminhos e contratos próprios descritos em suas entradas.

| Campo de `Result` | Tipo / significado |
|---|---|
| `schema_version` | Inteiro, atualmente 1 |
| `plugin_id` | ID canônico, mesmo quando selecionado por alias |
| `status` | success, failed, unavailable, partial ou cancelled |
| `started_at`, `finished_at` | Strings ISO 8601 em UTC; término preenchido na finalização |
| `parameters` | Objeto dos parâmetros do plugin, com caminhos/IPs serializados; não inclui format/output_dir |
| `findings` | Lista de objetos específicos da ferramenta; não há esquema único por achado |
| `errors` | Lista de mensagens textuais |
| `artifacts` | Lista de caminhos absolutos de arquivos existentes, incluindo o próprio result.json quando gravado |
| `attack` | Lista de relações tactic, technique, source, rationale e context opcional |

O filtro de parâmetros remove chaves que contenham `password`, `secret` ou `token`; não sanitiza automaticamente conteúdo de achados, query strings, caminhos ou saída de backends. `auth_file` permanece como caminho. Não passe segredos em campos livres esperando redação automática.

Exemplo **sintético e ilustrativo**, sem representar execução real (caminhos substituíveis):

```json
{
  "plugin_id": "tcp_scan",
  "status": "success",
  "schema_version": 1,
  "started_at": "2026-01-01T12:00:00+00:00",
  "finished_at": "2026-01-01T12:00:01+00:00",
  "parameters": {"target": "127.0.0.1", "ports": [8000], "context": "internal", "timeout": 3, "workers": 16},
  "findings": [{"host": "127.0.0.1", "port": 8000, "status": "open"}],
  "errors": [],
  "artifacts": ["/CAMINHO_DO_LAB/outputs/tcp_scan/ID_DA_EXECUCAO/result.json"],
  "attack": [{"tactic": "TA0007", "technique": "T1046", "source": "https://attack.mitre.org/techniques/T1046/", "rationale": "Comportamento documentado no catálogo de portabilidade", "context": "internal"}]
}
```

| Código CLI | Significado |
|---|---|
| 0 | `success`; comandos de consulta também podem retornar zero com lacunas/dependências ausentes |
| 1 | `failed`; também erro de loader no `doctor` |
| 2 | Erro de parsing, opção/ID desconhecido; normalmente sem `result.json` |
| 3 | `unavailable`, inclusive tentativa de `run` em plugin antigo |
| 4 | `partial`; leia achados e erros antes de decidir repetir |
| 130 | `cancelled` no wrapper da execução automatizada |

Validação condicional durante execução costuma resultar em `failed` (1), não 2. Há diferenças: `ctx.error()` define `partial` mesmo sem achados; exceção genérica retorna `partial` se já existem achados, senão `failed`; ausência de root verificada como `Unavailable` resulta em 3. Achados de restauração também contam como achados. Falha ao escrever relatório pode alterar o estado para failed/partial e deixar `result.json` ausente ou incompleto. Leia stderr e código do processo além do JSON.

### Redirecionamento e leitura

```sh
# Requer apenas geração de consultas; não abre navegador nem pesquisa
python pyops.py run search_queries --query 'fixture exemplo' --format json --output-dir relatorios > resultado.json 2> diagnostico.log
codigo=$?
printf 'Código: %s\n' "$codigo"
```

`--format json` reserva stdout ao objeto resultado dos plugins novos; mensagens de loader ficam em stderr. `--format text` imprime o mesmo objeto com indentação. Parsing inválido, plugin antigo ou falha antes do wrapper podem deixar stdout vazio: não presuma JSON em todo retorno.

```python
# Processa um relatório já produzido, sem executar ferramenta
import json
from pathlib import Path

result = json.loads(Path("resultado.json").read_text(encoding="utf-8"))
if result["schema_version"] != 1:
    raise ValueError("Esquema não suportado por este consumidor")
print(result["plugin_id"], result["status"])
for error in result["errors"]:
    print("ERRO:", error)
for finding in result["findings"]:
    print(finding)
for artifact in result["artifacts"]:
    print("ARQUIVO:", artifact)
```

### Lote com controle de retorno

Este exemplo Python usa apenas referências locais, não depende de rede, não presume que todo retorno tem JSON e não usa shell. Salve como script no diretório do projeto ou adapte o caminho de `pyops.py`.

```python
import json
import subprocess
import sys

jobs = [
    ["network_reference", "--search", "rotas"],
    ["find_reference", "--search", "nomes"],
    ["vim_reference", "--search", "salvar"],
]
for job in jobs:
    completed = subprocess.run(
        [sys.executable, "pyops.py", "run", *job,
         "--format", "json", "--output-dir", "relatorios"],
        capture_output=True, text=True, check=False,
    )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        print(job[0], "sem JSON", completed.returncode, completed.stderr)
        continue
    print(job[0], completed.returncode, result["status"], result["artifacts"])
    if completed.returncode != 0:
        print(result["errors"], completed.stderr)
```

Para automatizar operações de rede, substitua a lista somente após preparar fixtures/escopo e considere os limites de cada ferramenta. Não paralelize alterações de forwarding/rotas/canais que compartilhem estado. Não use o código zero de `doctor` como única condição de prontidão: analise `plugins[].unavailable` e `operations` do perfil escolhido.

<a id="migracao"></a>
## 9. ATT&CK e migração OpS

A classificação é o recorte local declarado como **ATT&CK Enterprise 19.2** em [core/attack.py](../core/attack.py), sem atualização em runtime. Este manual descreve esse recorte, sem auditar sua atualização externa. A tabela de cada entrada reproduz as relações do código, incluindo seus limites: texto de categoria não substitui `ATTACK`, e referência não é execução de técnica.

Em TCP, Nmap e cabeçalhos HTTP, `internal` mantém T1046/TA0007 e `external` mantém T1595/TA0043 no resultado. A classificação depende da intenção/contexto declarado pelo operador, não da faixa do IP; endereço privado não escolhe contexto automaticamente. SMB e wireless refinam suas relações em execução conforme perfil/operação, como descrito no catálogo.

`matrix` enumera relações do catálogo. Uma tática sem relações vira linha `gap`. Entradas sem ATT&CK estruturado, inclusive a lacuna ARP, não ganham linha própria por esse motivo; consulte também `list`. Estado `unavailable` reflete checagem de dependências/razão declarada, e `experimental` é o estado geral do catálogo. No JSON, `validated` só é verdadeiro para `kind=tool`, `status=ready` e sem indisponibilidade; as entradas atuais não satisfazem `ready`. Mesmo esse campo não é um relatório de validação ambiental.

A migração conserva os aliases abaixo, não todo fluxo/prompt/arquivo do Bash. Um mesmo motor substitui as duas opções TCP. Identificadores sem namespace, salvo os aliases explicitamente existentes, não são atalhos OpS.

| OpS | Alias aceito | ID PyOpS | Natureza da migração |
|---|---|---|---|
| `001` | `ops:001` | [network_reference](#plugin-network_reference) | referência, não executa comandos |
| `002` | `ops:002` | [windows_reference](#plugin-windows_reference) | referência, não executa comandos |
| `003` | `ops:003` | [wsl_vbox_routes](#plugin-wsl_vbox_routes) | ferramenta experimental |
| `101` | `ops:101` | [document_metadata](#plugin-document_metadata) | ferramenta experimental |
| `102` | `ops:102` | [domain_intelligence](#plugin-domain_intelligence) | ferramenta experimental |
| `103` | `ops:103` | [reverse_dns](#plugin-reverse_dns) | ferramenta experimental |
| `104` | `ops:104` | [dns_records](#plugin-dns_records) | ferramenta experimental |
| `105` | `ops:105` | [search_queries](#plugin-search_queries) | ferramenta experimental |
| `106` | `ops:106` | [website_inventory](#plugin-website_inventory) | ferramenta experimental |
| `201` | `ops:201` | [dns_zone_transfer](#plugin-dns_zone_transfer) | ferramenta experimental |
| `202` | `ops:202` | [cname_inventory](#plugin-cname_inventory) | ferramenta experimental |
| `301` | `ops:301` | [wireless_lab](#plugin-wireless_lab) | ferramenta experimental |
| `601` | `ops:601` | [root_recovery_reference](#plugin-root_recovery_reference) | referência, não executa comandos |
| `602` | `ops:602` | [local_exposure_audit](#plugin-local_exposure_audit) | ferramenta experimental |
| `603` | `ops:603` | [vim_reference](#plugin-vim_reference) | referência, não executa comandos |
| `604` | `ops:604` | [restricted_shell_reference](#plugin-restricted_shell_reference) | referência, não executa comandos |
| `801` | `ops:801` | [arp_mitm_lab](#plugin-arp_mitm_lab) | ferramenta experimental |
| `901` | `ops:901` | [tcp_scan](#plugin-tcp_scan) | ferramenta experimental |
| `902` | `ops:902` | [tcp_scan](#plugin-tcp_scan) | ferramenta experimental |
| `903` | `ops:903` | [http_headers](#plugin-http_headers) | ferramenta experimental |
| `904` | `ops:904` | [smb_inventory](#plugin-smb_inventory) | ferramenta experimental |
| `905` | `ops:905` | [linux_inventory](#plugin-linux_inventory) | ferramenta experimental |
| `906` | `ops:906` | [filesystem_audit](#plugin-filesystem_audit) | ferramenta experimental |
| `907` | `ops:907` | [find_reference](#plugin-find_reference) | referência, não executa comandos |
| `908` | `ops:908` | [nmap_scan](#plugin-nmap_scan) | ferramenta experimental |
| `909` | `ops:909` | [arp_discovery](#plugin-arp_discovery) | ferramenta experimental |
| `1001` | `ops:1001` | [legacy_arp_agent](#plugin-legacy_arp_agent) | lacuna indisponível |

`001` sem `ops:` é alias adicional de `tcp_scan`. `043`, `080` e `tcp_rev_shell` são entradas antigas do PyOpS, sem aliases OpS. Os módulos indisponíveis de `043`, táticas sem relações e `legacy_arp_agent` devem ser tratados como lacunas, não capacidades de cobertura implícita.

<a id="diagnostico"></a>
## 10. Diagnóstico e manutenção

| Sintoma | Verificação e ação |
|---|---|
| `pyops` não encontrado | Ative a venv e instale o projeto; confira `python -m pip show owl-pyops`; use `python pyops.py --help` no checkout |
| Pacote Python ausente | Instale o extra no mesmo interpretador usado para executar; nome importável `dns` vem de dnspython e `bs4` de beautifulsoup4 |
| Executável ausente | Confira PATH e pacote da distribuição; repita `info ID`/`doctor`; elevação pode alterar PATH/venv |
| `doctor` zero, ferramenta falha | Inspecione dependências por operação, permissões, topologia e requisitos condicionais; zero só indica ausência de erros do loader |
| Erro `Loader:` | Revise stderr e `loader_errors`; entradas podem estar faltando; não considere o catálogo completo até corrigir importação/metadados |
| Argumentos não reconhecidos | Consulte `run ID --help`; opções de `run` devem vir depois do ID; menu não aceita format/output-dir |
| Condição inválida com código 1 | Campos exigidos por operação e limites adicionais são validados após parsing; leia `errors` |
| Timeout / backend termina cedo | Confira alcance, backend e duração; ajuste timeout onde existe; tempo por consulta não limita lote inteiro; capture/discover/MITM esperam backend vivo até o prazo |
| TLS inválido | Confira relógio, nome do certificado, cadeia e confiança da fixture; não existe flag para desabilitar validação TLS |
| HTTP 403/429, busca vazia, CT não JSON | Preserve erro; use fixture ou entrada local/URL explícita quando suportada; bloqueio não comprova ausência de dados |
| HEAD 405 mas site responde | `http_headers` não troca automaticamente para GET; interprete como limitação dessa coleta |
| Permissão negada | Confira leitura das entradas, escrita no output, privilégios do backend e capacidades da interface; elevar toda operação não é requisito universal |
| SMB auth-file recusado | Confira existência e bits de grupo/outros; prefira filesystem Linux e `chmod 600`; Nmap não recebe essas credenciais |
| Interface/canal ausente | Compare nome com `doctor`, `ip` e `iw`; confirme camada 2, hardware e canal antes da sessão |
| Inventário parcial em WSL/container | Verifique namespace, arquivos `/proc`/`/etc`, executáveis e disponibilidade de systemd; seções restantes ainda são úteis |
| Saída vazia / nenhuma porta aberta | Leia escopo, limites, status individuais e erros; não conclua ausência de exposição |
| Relatório parcial | Leia `status`, `errors`, artefatos existentes e indicadores de restauração; repita somente a etapa necessária após corrigir causa |
| JSON inexistente/inválido | Confira código 2/3, stderr, disco/permissões e interrupção na escrita; stdout de `info` não é JSON único |
| Arquivo backend incompleto | Consulte TXT/XML/PCAP e prazo/cancelamento; presença em artifacts não garante conteúdo completo |
| Rede alterada após interrupção | Use estado da sessão e procedimentos de restauração; SIGKILL/queda não executa finally |

### Verificação local e atualização

Para conferir a instalação sem operar alvos:

```sh
python pyops.py --help
python pyops.py list --format json
python pyops.py info wireless_lab
python pyops.py doctor
python pyops.py matrix --format json
```

Do diretório `owl-PyOpS/`, com extra dev instalado:

```sh
# Unitários: configuração padrão exclui integration e fixtures bloqueiam rede externa
python -m pytest -q
# Opcional: backends reais em loopback e arquivos sintéticos
python -m pytest -q -m integration
```

Os unitários usam simulações em vários backends: passar testes não comprova permissões, driver, camada 2 ou interoperabilidade real. Integrações exigem dependências e recursos locais; podem abrir serviços loopback e usar Nmap/ExifTool. Não execute testes de laboratório reais só para validar documentação. MITM, deauth e mudanças de rede precisam de validação ambiental separada.

Após atualizar um checkout revisado, reative a venv e execute `python -m pip install -e '.[all,dev]'` (ou somente os extras usados), repita `doctor`, ajuda e testes pertinentes. A instalação editável reflete o código do checkout; mantenha código, dependências e manual da mesma revisão. Preserve alterações locais antes de atualizar e não use comandos destrutivos para “limpar” relatórios.

Fontes principais para manutenção: [CLI](../core/cli.py), [contrato de resultados](../core/operations.py), [validação](../core/validation.py), [base dos plugins](../plugins/base.py), [DNS](../plugins/recon/dns_tools.py), [web](../plugins/recon/web_tools.py), [rede](../plugins/discovery/network.py), [inventário local](../plugins/discovery/local.py), [SMB](../plugins/discovery/smb.py), [rede de laboratório](../plugins/lab/network_lab.py), [wireless](../plugins/lab/wireless.py) e [referências](../plugins/reference/guides.py). O [plano de portabilidade](plano-portabilidade-attack.md) registra intenções e lacunas; uma intenção ali não substitui comportamento implementado.

[Voltar ao sumário](#sumario)
