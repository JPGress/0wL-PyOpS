# OwL PyOpS — Python Operator's Script

Toolkit de laboratório em Python, sucessor modular do [owl-ops](../owl-ops/README.md). A portabilidade usa o comportamento das ferramentas como referência e organiza o catálogo pelo **MITRE ATT&CK Enterprise 19.2**. Os scripts Bash não são executados como backend.

A migração acrescenta CLI automatizável, aliases do OpS, resultados JSON e plugins para DNS, web, documentos, descoberta de rede, inventário local, SMB e operações delimitadas de laboratório. Guias são identificados como referências; opções sem implementação são lacunas. Os plugins permanecem **experimentais** até completar sua matriz de validação ambiental. Isso inclui operações que já passaram em testes locais.

## Instalação

Python **3.11 ou superior**, em Linux/Kali ou WSL2:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dns,web,dev]'
python pyops.py doctor
```

O núcleo não exige bibliotecas externas. Extras disponíveis: `dns`, `web`, `socmint`, `dev` e `all` (dependências de funcionalidades, sem pytest). Dependências opcionais ausentes não fazem o plugin desaparecer.

Backends são instalados separadamente pelo operador: Nmap, ExifTool, WHOIS, iproute2, arp-scan, smbclient/rpcclient, tcpdump, arpspoof e suíte Aircrack-ng conforme a ferramenta escolhida. `doctor` mostra requisitos por plugin/operação; ele não instala pacotes, testa alvos ou modifica a rede. Interface wireless e acesso à camada 2 dependem do hardware/topologia disponíveis, inclusive no WSL2.

## Uso

```sh
# Menu interativo
python pyops.py

# Catálogo, ajuda, dependências e classificação
python pyops.py list --tactic TA0043
python pyops.py info dns_records
python pyops.py matrix --format markdown

# Consulta usando nome estável ou alias do Bash
python pyops.py run dns_records --domain example.test --types A MX --format json
python pyops.py run ops:104 --domain example.test --types A MX

# Referências não executam os comandos exibidos
python pyops.py run ops:001 --search rotas

# Análise de documento sintético local
python pyops.py run document_metadata --files ./fixture.pdf
```

`example.test` representa uma fixture do seu laboratório; não pressupõe um serviço DNS disponível. Para scanning, informe alvo, portas e contexto `internal` ou `external`. O programa não inicia varreduras somente por abrir o menu.

Todos os aliases antigos estão no namespace `ops:`. `ops:001` abre a referência de rede; `001` mantém o atalho PyOpS de reconhecimento, agora associado ao scanner TCP real. `ops:901` e `ops:902` compartilham o mesmo motor Python. `043`, `080` e `tcp_rev_shell` permanecem interativos; `run` não os transforma silenciosamente em sessões interativas.

Resultados ficam em `outputs/<plugin_id>/<run_id>/`, com JSON, arquivos especializados e permissões privadas quando suportadas pelo filesystem. O modo `--format json` reserva stdout ao resultado. Saídas e clientes gerados são ignorados pelo Git; dados locais preexistentes não são apagados.

Códigos de saída: `0` sucesso, `1` falha operacional, `2` erro de parsing dos argumentos, `3` indisponibilidade, `4` resultado parcial e `130` cancelamento. Validações condicionais feitas durante a execução retornam falha operacional com mensagem explicativa.

## Testes

```sh
# Unitários: rede externa bloqueada pelas fixtures
python -m pytest -q

# Integrações opt-in: somente loopback e arquivos sintéticos
python -m pytest -q -m integration
```

A suíte de integração abre serviços apenas em `127.0.0.1`, consulta DNS sintético, verifica HTTP/TCP, executa Nmap contra uma porta da fixture e ExifTool sobre documento sintético. Ela não executa MITM, deauth, mudanças reais de rotas ou consultas a alvos externos.

## Documentação

- [Manual do operador — instalação, comandos e catálogo completo](docs/manual-do-operador.md)
- [Plano executável, matriz de portabilidade e estado dos lotes](docs/plano-portabilidade-attack.md)
- [Arquitetura e contrato de execução](docs/architecture.md)
- [Como desenvolver plugins](docs/plugin_tutorial.md)
- [Baseline dos scripts de origem](docs/migration-baseline.json)

Use apenas ambientes e alvos autorizados. Os mapeamentos ATT&CK descrevem comportamentos associados e não certificam cobertura integral de técnicas.
