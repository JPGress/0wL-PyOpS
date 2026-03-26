# Guia Definitivo: Desenvolvendo Plugins para o 0wL PyOpS

Bem-vindo ao guia de desenvolvimento do **0wL PyOpS**. Este documento foi desenhado para ensiná-lo passo a passo como expandir as capacidades deste *framework* de cibersegurança do absoluto zero à maestria ofensiva.

---

## 1. A Filosofia do Auto-Discovery

O PyOpS não é um script monolítico onde você insere funções dentro de blocos cruéis de código como extensos `if/else`. Ele é um **Framework Modular Orientado a Plugins**. 

O núcleo sistêmico (`core/`) atua unicamente renderizando interfaces, cores, despachando comandos do mouse e aguardando *input*. Ele **nunca** sabe quantas armas ou ataques existem. A mágica acontece através de um fenômeno batizado de **Auto-Discovery**: Assim que você cria qualquer arquivo `.py` solto dentro da pasta `plugins/` herdando as leis base do sistema, o inicializador o localiza em tempo de inicialização, extrai seus metadados e pinta na tela inteiramente sozinho. 

Você nunca precisa encostar em arquivos centrais se tudo o que você deseja é adicionar uma nova ferramenta.

---

## 2. A Classe Base Obrigatória (`plugins/base.py`)

Para o núcleo injetar a sua ferramenta perfeitamente na interface final, ela precisa obedecer rigorosamente ao molde estrito presente em `plugins.base.BasePlugin`. Este contrato dita os parâmetros obrigatórios.

### Atributos Mínimos Necessários
- **`PLUGIN_ID`**: A chave numérica em String que os operadores escolherão para engatilhar o script (ex.: `"002"`).
- **`NAME`**: A manchete que brilhará no CLI para o usuário (ex.: `"SSH Bruto-Force"`).
- **`GROUP`**: O agrupador da aba tática. Escolha entre `"Red"`, `"Blue"`, `"Purple"` ou `"Misc"`.
- **`TACTIC`**: Identificador categorizado do framework MITRE (ex.: `"TA0001"` para *Initial Access*).
- **`DESCRIPTION`**: Uma frase objetiva com ajuda/contexto para o usuário final que vai operar sua ferramenta.

---

## 3. Mão de Obra: Criando Seu Primeiro Ataque

Vamos arquitetar um scanner de portas fictício e introduzi-lo na tática de **Discovery (TA0007)** como membros do **Red Team**.

### Passo A: Criando a Estrutura
Navegue pelo painel lateral, localize o repositório lógico: `plugins/attack/` e instancie um novo arquivo, por exemplo: `port_scanner.py`.

### Passo B: Incorporando dependências Nativas
Você necessariamente precisa importar o molde obrigatório e as ferramentas de impressão gráfica seguras da arquitetura.

```python
from plugins.base import BasePlugin
from core.logger import log
```

### Passo C: Desenvolvendo o Tático
Crie a Classe que reflete o Metadado, seguida do coração da inteligência técnica contida invariavelmente dentro da função vitalícia `run(self)`:

```python
class QuickPortScannerPlugin(BasePlugin):
    # Metadados lidos pelo core/registry.py
    PLUGIN_ID = "002"
    NAME = "Fast TCP Port Scanner"
    GROUP = "Red"
    TACTIC = "TA0007"
    DESCRIPTION = "Executa uma exploração rápida de blocos TCP em IPs para mapeamento primitivo."

    # A lógica letal encapsulada do plugin
    def run(self):
        log.info("Inicializando socket TCP no alvo...")
        
        #
        # O SEU CÓDIGO DE TRABALHO TÉCNICO VEM AQUI
        # (Ex: socket.connect_ex((ip, porta)), nmap_import, etc)
        # 
        import time 
        time.sleep(1) # Simulando rede
        
        # Testando comunicações através da formatação limpa da CLI
        log.warning("As portas 21 e 22 encontram-se expostas ou filtradas.")
        time.sleep(1)
        log.success("Scan executado sem anomalias. Concluído!")
```

---

## 4. Evite Crimes Visuais: O Logger (`core/logger.py`)

No contexto do **0wL**, comandos primitivos como `print()` estropearão toda a harmonia estética e ANSI de terminal *Dark* que o framework projeta. Em contrapartida, use ativamente a pre-formatação da variável `log`, disponibilizando 5 cores táticas exclusivas.

- `log.info("Processo iniciando...")` → Gera verde suave descritivo.
- `log.success("Root shell obtido.")` → Converte todo o bloco em verde fluorescente alertivo para comemoração!
- `log.warning("Timeout na comunicação remota.")` → Imprime texto em amarelo cítrico advertindo perigo de instabilidade.
- `log.error("Permissão Negada.")` → Evidencia as palavras em vermelho carmesim relatando quebra trágica de continuidade.
- `log.debug("A struct TCP falhou em carregar socket C.")` → Cinza grafite, passa esquecido pelas vistas do usuário para documentação fria.

Ao pedir capturas do usuário, como injetar um IP, procure fazê-lo envolvendo blocos de `try-except KeyboardInterrupt`, capturando tentativas de fechar pelo `Ctrl+C` com respostas silenciosas que impedirá o temido rastreamento sujo vermelho do `Traceback` de Python se apresentar e vazar contexto pro usuário final.

---

## 5. Coroando e Opcional: A Verificação

Finalizada as digitações no seu código de plugin `port_scanner.py`, nem mesmo feche o aplicativo ou avise bibliotecas. Apenas salve-o e reinicialize de imediato o framework:

```bash
python3 pyops.py
```

O sistema automaticamente reconhecerá os códigos binários importados localmente, interpretará o número alocado (`TA0007`) e organizará a arquitetura gráfica de opções dentro de uma recém recriada aba do **[ RED TEAM ]**. 

Se você entrar no prompt estelar com `002`, o `core/dispatcher.py` imobilizará a linha neutra e passará a agulha de execução imediatamente para o corpo do seu método `run()`, permitindo suas lógicas atuarem e devolvendo o controle da sessão perfeitamente assim que seu script falecer. 

E tudo isso sem precisar escrever uma única linha de *array* ou refazer importação global dos construtores centrais!
