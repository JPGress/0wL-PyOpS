# Task List: Refatoração Modular PyOpS

- [x] **1. Estrutura Base e Configurações de UX**
  - [x] Criar diretório `core/`.
  - [x] Criar arquivo `core/config.py` exportando paleta de cores, estilos visuais e constantes estéticas (substituindo a classe `C`).
  - [x] Migrar strings base e constantes estáticas (`VERSION`, `RELEASE`) para a configuração.

- [x] **2. Sistema de Logging**
  - [x] Implementar `core/logger.py` para padronizar logs.
  - [x] Adicionar níveis de log: info, warning, erro, success e opcional suporte a log file.

- [x] **3. Registro de Operações e Plugins (Registry)**
  - [x] Criar `core/registry.py` com lógica (padrão Registry/Singleton) para armazenar metadados dos comandos/plugins.
  - [x] Estruturar formato de dados exigido (ex: ID, Grupo, Tática, Descrição, Referência da Função).

- [x] **4. Autoload/Plugins Manager**
  - [x] Criar o pacote `plugins/` contendo os subdiretórios `attack/`, `d3fend/`, `purple/` e `misc/`.
  - [x] Implementar carregamento dinâmico (auto-discovery) que importe os arquivos e chame o registro no `registry.py`.

- [x] **5. Interface de Menu (UX/UI Renderization)**
  - [x] Desenvolver `core/menu.py` responsável por exibir Headers e Banners via `config.py`.
  - [x] Desenvolver lógica de renderização seccionada dinamicamente consultando o Registry. A interface renderizará em 4 grupos: **Red**, **Blue**, **Purple** e **Misc**, organizando pelas respectivas funções de cada plugin.

- [x] **6. Dispatcher de Ações**
  - [x] Desenvolver `core/dispatcher.py` acoplando iterativamente: loop de Input, Busca da opção validada no Registry e Invocação da Função (com catch de exceções).

- [x] **7. Ponto de Entrada (Entrypoint)**
  - [x] Refatorar o antigo `pyops.py` (entrypoint principal) removendo a vasta quantidade de `print()` hardcoded e convertendo-o apenas no script que importa o `core/` e inicia o CLI chamando o renderizador e o dispatcher.
