# Documentação de Arquitetura: 0wL PyOpS

Este documento detalha a topologia atual do projeto **0wL PyOpS**, sua lógica interna de funcionamento e as regras para escalabilidade de novas <i>features</i>.

---

## 1. Visão Geral da Arquitetura
A arquitetura do PyOpS é baseada num modelo **Modular / Orientado a Plugins**. Em vez de existir um único <i>script</i> gigante com incontáveis condições (`if/else`), o projeto foi fatiado. 

O coração do sistema (`core`) gerencia exclusivamente a renderização e o tráfego de dados, sem saber *o que* os ataques ou defesas fazem. Toda a lógica ofensiva e defensiva fica externalizada no diretório `plugins/`. Isso permite que o desenvolvimento do framework e dos recursos operacionais caminhem de forma independente.

---

## 2. Estrutura de Diretórios e Arquivos

Abaixo apresentamos o papel de cada pasta e arquivo presente no diretório. Múltiplos arquivos terminados em `.md` (como `task.md`, `walkthrough.md`, `implementation_plan.md`) referem-se estritamente aos artefatos de controle de desenvolvimento.

### A Raiz (`./`)
Ponto base da aplicação.
* **`pyops.py`**: É o **Entrypoint**. Sua única atribuição é agir como um injetor/loader: importa o núcleo e aciona a ignição (ex.: `Dispatcher.run()`).
* **`tests/`**: O diretório dedicado ao controle de qualidade (Q&A). Abriga componentes do *pytest* validando a estabilidade da orquestração principal (como atestado por `test_dispatcher.py` e `test_plugin_loader.py`).
* ~~**`pyops/`**: Trata-se de um diretório ou pacote em "fase de transição/legado" contendo apenas subdiretórios de cache gerados no passado (`__pycache__`). Este diretório não é ativamente importado pela aplicação modular hoje.~~ \[CORRIGIDO]

### O Núcleo do Sistema (`core/`)
Lida unicamente com infraestrutura e interface de usuário. É o "chassi" do carro.
* **`config.py`**: Guarda metadados do aplicativo, banners em ASCII e a paleta de cores padrão (Dicionário ou Classe `C`).
* **`logger.py`**: Abstrai os modos de exibição e os padroniza (Mensagens de Sucesso, Aviso, Erro, Informação) evitando quebras do formato visual da ferramenta.
* **`registry.py`**: O cérebro do estado volátil. Trata-se de um Singleton/Storage. Carrega na memória RAM "quem" está habilitado, "como" acionar a função e a qual táctica/grupo tal script pertence.
* **`menu.py`**: Módulo estritamente cosmético encarregado de ler o `registry` e formatar as seleções para o usuário sob formato de interface em linha de comando (CLI).
* **`dispatcher.py`**: É o volante do usuário. Implementa o _loop infinito_ de captação de Input (`>` "Enter option:") e decide atrelar este input à exata função estocada na base ou reportar erro.

### Os Motores de Operação (`plugins/`)
Armazenam estritamente habilidades ou armas individuais. É o "motor" do carro.
* **`base.py`**: Dispõe da classe abstrata/mãe que define a interface e parâmetros rigorosos (ID, Nome, Classe de Grupo) de integração.
* **`attack/`**: Subdiretório para ofensiva contendo a pasta de cada tática do **MITRE ATT&CK** (como `recon.py`).
* **`d3fend/`**: Subdiretório de scripts e ferramentas do **Blue Team / MITRE D3FEND**.
* **`purple/` e `misc/`**: Destinados à verificação/emulação de adversário mesclada, bem como ferramentas miscelâneas que não se enquadram perfeitamente em nenhuma <i>framework</i> tática explícita.

---

## 3. A Lógica de Execução e Fluxo (Pipeline)

A aplicação inicializa-se de forma elegante:

1. **Auto-Discovery:** No início da execução (dentro de `pyops.py` ou via um loader dinâmico importado pelo mesmo), uma varredura sistêmica é feita na pasta `plugins/`.
2. **Auto-Registro:** Todo `.py` que extenda `base.py` sofre injeção imediata no dicionário armazenado em `core/registry.py`.
3. **Mapeamento:** O aplicativo processa o agrupamento dos dados separando-os entre: Red (Attack), Blue (D3fend), Purple ou Misc, salvando e indexando a chave que engatilha eles (O ID do usuário, ex: `"001"`).
4. **Prontidão de Comando:** `core/menu.py` lista na tela de forma limpa todas as táticas carregadas ativas e o `core/dispatcher.py` imobiliza a execução pendente e à espera de um sinal do operador.
5. **Execução:** Dada a seleção do terminal, o código é chamado e exibe *loggers*, finalizando o script ou voltando ao menu.

---

## 4. Onde criar os futuros arquivos?

* **Novos Comandos de Interface ou Mecânicas Internas:** Se quiser adicionar "suporte a atalhos de teclado", "traduções na linguagem", ou conectar um banco SQLite, aloque logicamente em `core/`.
* **Novas Técnicas Ofensivas ou Scanners:** Se escreveu um script de _Wordlist Generator_ ou _SSH Brute-Force_, isso deve se tornar uma classe herdada construída em `plugins/attack/<nome_da_ferramenta>.py`.
* **Novos Testes Automatizados:** Todo arquivo que garanta a integridade estrutural, a saúde da ingestão de inputs (`dispatcher`) ou do sistema de descobrimento, deve continuar a repousar no diretório `tests/` para rodar na esteira CI/CD local pelo Pytest.
* **O Diretório `pyops/`**: Pode ser fisicamente apagado (ou `rm -rf pyops/`) para livrar o projeto da sujeira de refatoração, a menos que ele abranja um segundo pacote python ativo.
