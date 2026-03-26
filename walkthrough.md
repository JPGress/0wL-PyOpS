# Walkthrough: Desenvolvimento do OwL's Eyes (Projeto Piloto)

## 📌 Resumo da Entrega
Criamos a estrutura fundamental do módulo **OwL's Eyes** para ser utilizado como um projeto piloto do *Purple Team* no framework `0wL PyOpS`. Os objetivos estabelecidos e a arquitetura delineada na base intelectual original foram fielmente transplantados para o ecossistema local na forma de plugins auto-descobríveis.

## 🛠️ Mudanças Realizadas

1. **Injeção no Ecossistema PyOpS:**
   * Criado o arquivo `plugins/purple/owls_eyes.py` herdando da classe abstrata `BasePlugin`.
   * Configurado com os Metadados: `PLUGIN_ID = "043"`, `NAME="Personal Attack Surface Management"`, `GROUP="Purple"` e `TACTIC="TA0043"`.
   * Construído o **Hub Interativo**, um Sub-Menu CLI acionado pela função `run()` com suporte à saída suave `try-except KeyboardInterrupt`, integrando todos os 7 módulos subsequentes previstos pela teoria da ferramenta.

2. **Modularização de Lógicas:**
   * Criada a pasta `plugins/purple/owls_eyes_modules/` que funciona como o cérebro das funcionalidades. 
   * A modularização permite que a ferramenta evolua futuramente permitindo múltiplos programadores atuarem de forma independente em diferentes áreas sem afetarem o arquivo primário.
   * Criados arquivos vazios (Placeholders) com avisos de "Piloto" via `core.logger` para as demais features conceptuais (Módulos 1, 4, 5, 6 e 7).

3. **Construção do Minimum Viable Product (MVP):**
   * **Module 2 (SOCMINT & Identity) [FASE 2 COMPLETA]**: 
     - **Instagram**: Integrado via `instaloader`. Detecta perfis privados e sugere OPSEC (uso de sock puppets). No modo público, possui a Coleta **Rápida** (bio, followers, últimas 10 fotos e legendas) e a Coleta **Completa** (Itera centenas de seguidores/seguidos - *Requer sessão instaloader pré-configurada para não falhar com LoginRequired*).
     - **LinkedIn**: Para evitar Auth-Walls extremas na coleta deslogada, usamos `requests` e `BeautifulSoup` para fazer *Google Dorking* no perfil (ex: `site:linkedin.com/in/ "user"`) e raspamos os snippets do Google com o resumo das atividades profissionais.
     - **Arquivo .JSON**: Todas as informações são compiladas em tempo real em formato dict e salvas no disco sob a assinatura (e.g. `target_neymarjr_169..._socmint.json`).
   * **Module 3 (Digital Footprint & Devices)**: Rastreamento similar implementado no arquivo `mod3_footprint.py`, colhendo entradas de domínio (*FQDN*) e registrando comemorações modulares simuladas.

## ✔️ Validação de Arquitetura

O sistema de **Auto-Discovery** testado em `/pyops.py` identificou com êxito os metadados recém-criados, imprimindo as informações perfeitamente customizadas no CLI e listando `OwL's Eyes` sob a insígnia tática `[ PURPLE TEAM ]`. A escolha do sub-módulo gerencia o controle da interface de forma íntegra e bloqueia devidamente interações erradas, garantindo uma demonstração enxuta, confiável e limpa para qualquer evento de Pilot Project.
