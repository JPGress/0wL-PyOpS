# Desenvolvendo um plugin automatizável

Crie um módulo na família apropriada de `plugins/`. O loader registra classes definidas nesse módulo que herdem de `BasePlugin` e tenham ID preenchido. Helpers compartilhados podem ser classes sem ID; não serão registrados.

```python
from plugins.base import BasePlugin

class ExamplePlugin(BasePlugin):
    PLUGIN_ID = "example_reference"
    ALIASES = ("example:guide",)
    NAME = "Guia de exemplo"
    DESCRIPTION = "Demonstra o contrato de plugins sem operação externa."
    GROUP = "Misc"
    TACTIC = "Reference"
    KIND = "reference"
    STATUS = "experimental"

    def add_arguments(self, parser):
        parser.add_argument("--topic", required=True)

    def execute(self, parameters, context):
        context.finding(topic=parameters["topic"], text="Conteúdo de exemplo")
```

Verifique com:

```sh
python pyops.py info example_reference
python pyops.py run example_reference --topic instalação --format json
```

## Regras de implementação

- Declare entradas com argparse e use os validadores compartilhados para domínios, hosts, URLs e portas. Não permita que um alvo se transforme em opção de backend.
- Use `context.finding(...)`, `context.error(...)` e `context.artifact(nome, conteúdo)`. Para backend que grava arquivo, reserve o caminho com `context.artifact(nome)`.
- Use `core.operations.command(argv, timeout=...)` para backends curtos e `Process` para processos supervisionados. Não use `shell=True`.
- Declare dependências como `(("python", "requests"), ("executable", "exiftool"))`. Dependências condicionais podem usar `OPERATION_DEPENDENCIES` e `OPERATION_KEY`.
- Não importe dependências opcionais no topo do módulo. Importe-as dentro da execução, após a checagem de disponibilidade.
- As relações `ATTACK` devem conter tática, técnica, fonte, justificativa e, quando necessário, contexto. Novas técnicas exigem revisão do recorte ATT&CK e testes da relação.
- Não faça rede, configurações do sistema ou leitura de dados operacionais durante descoberta/importação.
- Preserve achados parciais, encerre seus próprios processos e restaure alterações temporárias em `finally`.
- Um guia não executa seus exemplos. Uma verificação de configuração não deve afirmar exploração bem-sucedida.

## Aceite

Inclua testes de sucesso, falha e interrupção com fixtures sintéticas. Use o marcador `integration` somente para testes explicitamente locais ou documentados. Mantenha `STATUS = "experimental"` até completar as integrações relevantes e registrar a evidência na matriz de portabilidade.

Adicionar um plugin não exige editar o dispatcher ou o menu. IDs e aliases repetidos são erros, não sobrescritas silenciosas.
