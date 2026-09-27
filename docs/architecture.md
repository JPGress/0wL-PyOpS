# Arquitetura do OwL PyOpS

## Fluxo

`pyops.py` → CLI → loader/registry → plugin → serviço Python/backend → resultado e artefatos.

O núcleo gerencia argumentos, catálogo, apresentação, subprocessos e relatórios. A lógica operacional reside nos plugins. A implementação de um plugin automatizável não lê `input()` nem imprime resultados diretamente: recebe parâmetros e publica achados pelo contexto.

O menu conserva as categorias Red, Blue, Purple e Misc, mas deriva as táticas dos metadados ATT&CK. Um plugin pode aparecer em mais de uma tática; isso não cria registros de execução duplicados. Referências e utilitários sem técnica aplicável têm categorias próprias.

## Contrato

`BasePlugin` fornece `PLUGIN_ID`, `ALIASES`, `NAME`, `DESCRIPTION`, `GROUP`, `KIND`, `STATUS`, `ATTACK`, `DEPENDENCIES` e dependências condicionais por operação. Implementações novas sobrescrevem:

- `add_arguments(parser)`: declara entradas para argparse.
- `execute(parameters, context)`: realiza o trabalho e publica resultados.

`run()` apresenta ajuda, coleta os argumentos via uma linha no menu e usa exatamente o mesmo parser e executor da CLI. Plugins antigos que implementam apenas `run()` continuam no menu, mas não aceitam execução automatizada. O contrato evita misturar prompts com automações; não existe sandbox de plugins.

O registro valida metadados e colisões antes de modificar índices. A descoberta considera apenas classes definidas no próprio módulo, em ordem determinística. Recarregar reconstrói o registro sem duplicação. Falhas são guardadas e exibidas por `doctor`/stderr. Importações não devem executar rede, abrir listeners ou modificar o sistema.

## Execução e persistência

Cada execução tem diretório próprio, nomeado por UUID, dentro de `outputs`. O resultado contém:

- `schema_version`, `plugin_id`, `status`, horários de início/fim;
- parâmetros serializáveis, omitindo chaves de senha/token/segredo;
- relações ATT&CK correspondentes ao contexto selecionado;
- `findings`, `errors` e caminhos dos `artifacts` existentes.

Estados: `success`, `partial`, `failed`, `cancelled`, `unavailable`. Uma consulta DNS válida com NXDOMAIN é um achado, não uma exceção. Timeout ou bloqueio são explicitados. Um resultado parcial não equivale à conclusão de todas as verificações.

Subprocessos recebem listas de argumentos, stdin fechado e grupo de processos próprio. stdout/stderr são direcionados a arquivos temporários para evitar bloqueio de pipes; a leitura é limitada a 16 MiB por fluxo. XML, PCAP e outras saídas extensas usam artefatos dedicados. Timeout e cancelamento encerram o grupo pertencente à operação. SIGTERM é convertido em cancelamento durante a execução no thread principal, permitindo limpeza e relatório.

As rotinas de laboratório não executam `sudo` nem encerram processos por nome. Aplicação de rotas mantém mudanças até `revert`; falhas de aplicação disparam rollback. Sessões MITM restauram forwarding; wireless remove apenas a interface monitor criada pela própria sessão e restaura o canal conhecido. SIGKILL, desligamento e mudanças concorrentes do administrador não têm garantia de rollback; os arquivos de estado servem à recuperação.

## ATT&CK

O recorte de técnicas/táticas está fixado em 19.2 no código, com links oficiais. Não depende de baixar a matriz durante a inicialização. `matrix` inclui lacunas e não contabiliza guias como ferramentas validadas. `experimental` é independente de dependências instaladas: disponibilidade não é validação operacional.

## Testes e instalação

`pyproject.toml` define Python >=3.11, instalação via setuptools e extras opcionais. As fontes de teste estão em `tests/`; caches foram retirados do índice. Testes unitários bloqueiam conexões externas; integrações loopback são opt-in. Backends reais que exigem laboratório específico permanecem experimentais até haver evidência adicional.
