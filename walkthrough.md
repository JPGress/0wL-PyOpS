# PyOpS Modular Refactoring Walkthrough

## Resumo das Alterações
- O mockup base (`pyops.py`) monolítico foi refatorado em uma arquitetura flexível dividindo o projeto entre o `core/` e os `plugins/`.
- Foi originado o arquivo `core/config.py` para isolar a classe de cores (ANSI) e as configurações de tela (Banners ASCII e metadados).
- Foi implementado um padronizador de logs no pacote `core/logger.py` com atalhos de saída `info`, `warning`, `error` e `success`.
- O mecanismo central de controle (`core/registry.py`) recebeu formatação autônoma em cache (`PluginRegistry`) designando que novos scripts declarados via herança da classe abstrata `plugins/base.py` insiram seus ponteiros na aplicação no momento da inicialização (separados por grupo e tática: *TA0043*, etc.).
- O pacote de UI (`core/menu.py`) foi desenhado para renderizar os dados do registrador iterativamente sobre as strings `[ RED TEAM ]`, `[ BLUE TEAM ]`, `[ PURPLE TEAM ]` limitando-se unicamente aos mocks que de fato existem instalados.
- Um controlador (`core/dispatcher.py`) passou a lidar com *loops* infinitos bloqueando interrupções sujas no teclado e invocando a função atrelada ao número fornecido nativamente pelo `input()`.
- O entrypoint principal `pyops.py` agora trabalha com apenas 10 linhas abstraídas ligando as integrações modulares.

## O Que Foi Testado
- **Renderização da UI e Auto-Discovery**: Verificou-se que o pacote importou e compilou automaticamente o arquivo mock em `plugins/attack/recon.py`, montou o cabeçalho dinâmico e desenhou um grupo **RED TEAM** expondo suas opções. 
- **Execução do Dispatcher**: Validou-se a seleção do usuário `001`, que localizou e derivou seu callback interno sem intervenção de logs hardcoded, mostrando uma mescla eficiente das classes via terminal.
- **Encerramento Controlado**: Teste do exit signal (`000`) foi aprovado, escapando do app elegadamente com as notificações do `logger`.

## Resultados da Validação
```
  [ RED TEAM ] 

 [+] Network Scanning & Enumeration [TA0043]
         - The adversary is trying to gather information they can use to plan future operations.
         [001] Execute
         ---

 [>] Enter the option number (000 to exit): 001
[+] Selected: Network Scanning & Enumeration
 [+] Running Mock Network Reconnaissance...
 [*] Mockup Mode: Action simulated.
 [+] Network Scan completed!

 [>] Enter the option number (000 to exit): 000
 [+] Exiting...
```
A arquitetura encontra-se plenamente desacoplada e operacional, pronta para alocar novos scripts individualmente soltando-os nos diretórios-alvo em `plugins/`.
