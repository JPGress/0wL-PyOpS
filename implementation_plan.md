# [Goal Description]
Refatoração Modular do PyOpS

O objetivo é evoluir o mockup atual (`pyops.py`) para uma arquitetura modular flexível e escalável, focando em operações de segurança integradas. O script base baseava-se num único arquivo com funções *hard-coded*. A nova arquitetura suportará plugins baseados em táticas do MITRE ATT&CK e D3FEND, organizados em grupos.

A estrutura de diretórios passará a seguir o formato:
```text
pyops/
├── core/
│   ├── __init__.py
│   ├── config.py       # Configurações UX e constantes
│   ├── logger.py       # Gerenciamento de log padronizado
│   ├── registry.py     # Registro e metadados de opções (Singleton/Dict)
│   ├── dispatcher.py   # Roteador de execução iterativo p/ as ferramentas 
│   └── menu.py         # Renderização do CLI segmentado
├── plugins/
│   ├── __init__.py
│   ├── base.py         # Classe abstrata p/ plugins e metadados
│   ├── attack/         # Plugins Red Team (MITRE ATT&CK)
│   ├── d3fend/         # Plugins Blue Team (MITRE D3FEND)
│   ├── purple/         # Adversary emulation
│   └── misc/           # Utilitários globais 
└── pyops.py            # Entrypoint minimizado (Carregador)
```

## Proposed Changes

### core
A fundação do sistema que lidará com I/O, estética e gerenciamento dinâmico.

#### [NEW] core/config.py
- **Configuração baseada em UX**: Mover classe `C` de cores e o banner ASCII estático do antigo `pyops.py` para cá. Este módulo abstrairá detalhes estéticos/strings de escapes e irá oferecer variáveis e templates gerenciais para as telas de prompt (`[+]`, `[>]`) e interface.

#### [NEW] core/logger.py
- **Logging**: Implementar sistema padronizado para exibir requisições de terminal (como `info`, `error`, `warning`, `success`). O intuito é garantir que as saídas e exceções dos plugins nunca quebrem a visualização nativa do script. Opcionalmente, suporte para exportar o log para arquivos locais de auditoria.

#### [NEW] core/registry.py
- **Registro de Opções**: Construir o centro de indexação (Singleton ou dict global) que armazenará os plugins lidos na inicialização. Vai indexar por plugin: nome, descrição da ação, referência (*callback/pointer*), Tática correlata (ex. `TA0043`) e seu respectivo agrupador primário (Red/Blue/Misc/Purple).

#### [NEW] core/dispatcher.py
- **Dispatcher de Ações**: Responsável direto pelo ciclo de vida interativo (`while True`). Aguardará o `input()` validado perante as keys do `registry`. Assim que identificada uma opção válida, invocará a lógica encapsulada evitando que aborts (como `Ctrl+C`) disparam blocos sujos da stack nativa do Python, controlando as saídas com classe.

#### [NEW] core/menu.py
- **Renderização do Menu em 4 Grupos**: A visualização solicitará as chaves ativas presentes no *Registry* global e efetuará aglomerados dinâmicos baseados no filtro de grupo. Em vez da lista plana atual, organizará em: **Red**, **Blue**, **Purple** e **Misc**, formatando e posicionando o menu CLI harmoniosamente.

### plugins
Diretório raiz que é ativamente vasculhado (via `importlib` ou `pkgutil`) para auto-cadastrar funcionalidades.
#### [NEW] plugins/base.py
- Declara a interface `BasePlugin` e a estrutura/metadata que deve ser implementada por todo módulo de ataque ou defesa.

#### [NEW] plugins/attack/, plugins/d3fend/, plugins/purple/ e plugins/misc/
- **Plugins por táticas**: Onde cada script de ataque ficará confinado futuramente. Apenas criaremos as pastas e arquivos *mock* básicos com metadados e um print representativo.

### pyops.py
#### [MODIFY] pyops.py
Remoção de todo o código *hard-coded* de seções estáticas do *MITRE ATT&CK*. Conversão da rotina exclusiva em importador agnóstico dos módulos `core` e acionador central da classe principal da UI.

## Verification Plan

### Automated Tests
*Não se aplica unit-testing agressivo nesta prova de conceito inicial. O script foca fortemente na orquestração CLI/TUI.*

### Manual Verification
1. Lançar o aplicativo mock refatorado de seu repositório central:
   `python3 pyops.py`
2. **Avaliação Estética (UX/Menu)**: A UI reconstruída pelo `core/menu.py` obrigatoriamente exibirá as matrizes separadas formalmente em **[ Red ]**, **[ Blue ]**, **[ Purple ]** e **[ Misc ]** usando os Mocks em `plugins/*`, comprovando o auto-discovery.
3. **Avaliação Operacional (Dispatcher)**: Ao inserir dados numéricos nas opções que não existem, interceptar retornos coloridos de Warning do `logger` em vez de quebra. Ao preencher dados de módulo mock válidos, exibir a execução ativada e retornar ao prompt de I/O em formato estável.
4. **Tratamento Terminal (Exception/Logging)**: Ao enviar interrupções no prompt (KeyboardInterrupt), observar logs descritivos e a saída fluída `[-] Exiting...`.
