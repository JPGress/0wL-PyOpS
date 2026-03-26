# 0wL PyOpS - Python Operator's Script

**0wL OPS** é um toolkit avançado de Segurança Operacional (OpSec) baseado em Python, desenvolvido especificamente para testes de invasão (penetration testers), equipes de Red Team, Blue Team, Purple Team e pesquisadores de segurança. 

O objetivo principal da ferramenta é atuar como um **hub centralizado e modular**, permitindo a unificação, organização e execução de diversos scripts e ferramentas de segurança a partir de uma interface única e padronizada.

---

## 🎯 Objetivo da Ferramenta

No dia a dia de operações de segurança e testes de invasão, analistas lidam com dezenas de scripts soltos, ferramentas de OSINT, utilitários de rede e exploits. O **0wL PyOpS** resolve o problema da fragmentação ao fornecer:

- **Centralização:** Um único ponto de entrada para todas as suas ferramentas personalizadas.
- **Padronização:** Interface de usuário (UI/UX) e sistema de logs unificados para todas as operações.
- **Escalabilidade:** Uma arquitetura de plugins robusta que facilita a adição de novos módulos sem alterar o código principal.
- **Categorização Estratégica:** Ferramentas organizadas utilizando terminologias de mercado e frameworks reconhecidos (como MITRE ATT&CK e D3FEND).

---

## 🏗️ Arquitetura e Estrutura

O projeto abandonou a abordagem monolítica em favor de uma arquitetura modular, dividida em dois componentes principais: o **Core** (Núcleo) e o sistema de **Plugins**.

### 1. Core (`core/`)
Responsável pelas funcionalidades base do sistema, não possuindo lógica de ataque ou defesa.
- `registry.py`: Gerencia o registro dinâmico e o armazenamento em memória de todos os plugins carregados.
- `dispatcher.py`: Atua como o cérebro da iteração inicial. Lê a opção do usuário, busca no registro e invoca o callback (`run()`) correspondente do plugin.
- `menu.py`: Renderiza a interface do usuário no terminal de forma amigável, listando os plugins separados por categoria.
- `logger.py`: Fornece uma funcionalidade de log padronizada (info, erro, sucesso, aviso, debug) com esquema de cores consistente.
- `config.py`: Armazena variáveis globais de configuração, versão, constantes de cores de terminal e o *banner* da aplicação.

### 2. Sistema de Plugins (`plugins/`)
A funcionalidade real da ferramenta reside aqui. Os módulos são carregados dinamicamente na inicialização.
- Subdiretórios lógicos organizam a intenção do plugin:
  - **Attack / Red:** Ferramentas ofensivas, enumeração, exploits.
  - **D3FEND / Blue:** Ferramentas defensivas, análise, mitigação.
  - **Purple:** Emulação de adversários e detecção combinada.
  - **Misc:** Utilitários gerais (ex: subir servidores web rápidos, utilitários de rede).
- Todos os plugins herdam da classe `BasePlugin` (`plugins/base.py`) e devem implementar variáveis obrigatórias (`PLUGIN_ID`, `NAME`, `GROUP`, `TACTIC`, `DESCRIPTION`) e o método principal `run()`.

---

## 🔌 Como os Plugins Funcionam (Lógica Interna)

A mágica do **0wL PyOpS** está no seu carregamento dinâmico:

1. Ao iniciar, o `pyops.py` chama a função `load_plugins()` (em `plugins/__init__.py`).
2. O script percorre automaticamente (via *reflection*) as pastas dentro de `plugins/`.
3. Ele carrega as classes que herdam de `BasePlugin` e as registra no `PluginRegistry`, categorizando-as pelos Grupos (Red, Blue, Purple, Misc) e Táticas (ex: Reconhecimento, Exfiltração, etc.).
4. O `menu.py` consome o os dados do Registry para plotar a interface.
5. Quando o usuário digita a opção (ex: `001`), o `dispatcher.py` identifica o módulo através do `PLUGIN_ID` e executa a função `.run()` isoladamente.

---

## 🚀 Instalação e Uso

### Requisitos
- Python 3.6 ou superior.

### Download
Clone o repositório na sua máquina local:
```bash
git clone https://github.com/SeuUsuario/owl-PyOpS.git
cd owl-PyOpS
```

### Execução
Navegue até a raiz do projeto e execute o arquivo principal:
```bash
# Dar permissão de execução, se necessário:
chmod +x pyops.py

# Iniciar a ferramenta:
./pyops.py
# ou
python3 pyops.py
```

### Criando o Seu Próprio Plugin
Adicionar uma nova funcionalidade é extremamente simples e não exige alteração nos arquivos `core`:

1. Crie um arquivo Python (`meu_plugin.py`) na pasta apropriada (ex: `plugins/misc/`).
2. Importe o `BasePlugin`.
3. Defina as variáveis de classe e sobrescreva o método `run()`:

```python
from plugins.base import BasePlugin
from core.logger import log

class MeuPlugin(BasePlugin):
    PLUGIN_ID = "002"
    NAME = "Meu Novo Scanner"
    GROUP = "Red"
    TACTIC = "Reconnaissance"
    DESCRIPTION = "Descrição curta do que o plugin faz."

    def run(self):
        log.info("Iniciando o scanner...")
        # Adicione a lógica da sua ferramenta aqui!
        log.success("Scanner finalizado com sucesso!")
```
4. Ao rodar o `./pyops.py`, seu plugin estará automaticamente catalogado e pronto para uso no menu!

---

## 🛡️ Aviso Legal
Esta é uma ferramenta voltada para **fins educacionais** e uso profissional autorizado em ambientes onde haja consentimento prévio para a realização de testes de segurança. O autor não se responsabiliza pelo mau uso desta ferramenta.
