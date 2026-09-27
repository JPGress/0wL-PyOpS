"""Guias são conteúdo: nunca executam os comandos apresentados."""
from plugins.base import BasePlugin
from core.attack import mapping


class Guide(BasePlugin):
    GROUP = "Misc"
    TACTIC = "Reference"
    KIND = "reference"
    SECTIONS = {}

    def add_arguments(self, parser):
        parser.add_argument("--search", default="")

    def execute(self, p, ctx):
        for title, content in self.SECTIONS.items():
            if p["search"].lower() in (title + " " + content).lower():
                ctx.finding(section=title, text=content, executable=False)


class NetworkReference(Guide):
    PLUGIN_ID = "network_reference"
    ALIASES = ("ops:001",)
    NAME = "Referência de rede Linux"
    DESCRIPTION = "Comandos de consulta de interfaces, sockets, rotas e DNS."
    SECTIONS = {"Interfaces": "ip -br address; ip link show",
                "Conexões": "ss -lntup; ss -ant; lsof -i",
                "Rotas": "ip route show; ip neighbour show",
                "DNS": "resolvectl status; cat /etc/resolv.conf; dig example.test"}


class WindowsReference(Guide):
    PLUGIN_ID = "windows_reference"
    ALIASES = ("ops:002",)
    NAME = "Referência Windows"
    DESCRIPTION = "Referência Windows consultável sem executar comandos Windows."
    SECTIONS = {"Sistema": "systeminfo; hostname; whoami /all",
                "Arquivos": "dir /a; where nome; Get-ChildItem",
                "Processos": "tasklist; Get-Process; Get-Service",
                "Rede": "ipconfig /all; route print; netstat -ano; Get-NetFirewallRule",
                "Contas": "net user; net localgroup",
                "Registro": "reg query HKLM\\SOFTWARE"}


class FindReference(Guide):
    PLUGIN_ID = "find_reference"
    ALIASES = ("ops:907",)
    NAME = "Referência find"
    DESCRIPTION = "Exemplos de busca por nome, tipo, tamanho e permissões."
    ATTACK = (mapping("T1083"),)
    SECTIONS = {"Nomes": "find ./lab -type f -name '*.txt'",
                "Profundidade": "find ./lab -maxdepth 2 -type d",
                "Permissões": "find ./lab -type f -perm -4000; find ./lab -perm -0002",
                "Tamanho e data": "find ./lab -type f -size +10M; find ./lab -mtime -1"}


class VimReference(Guide):
    PLUGIN_ID = "vim_reference"
    ALIASES = ("ops:603",)
    NAME = "Referência Vim"
    DESCRIPTION = "Comandos de edição, navegação, pesquisa e saída do Vim."
    SECTIONS = {"Edição": "i insere; Esc retorna ao modo normal; dd remove linha; yy copia; p cola",
                "Navegação": "h/j/k/l; gg início; G fim; /texto pesquisa; n próximo",
                "Salvar e sair": ":w salva; :q sai; :wq salva e sai; :q! descarta alterações",
                "Histórico": "u desfaz; Ctrl+r refaz; :help abre ajuda"}


class RootRecoveryReference(Guide):
    PLUGIN_ID = "root_recovery_reference"
    ALIASES = ("ops:601",)
    NAME = "Recuperação administrativa de root"
    DESCRIPTION = "Guia de recuperação local; não altera boot, contas ou senhas."
    SECTIONS = {"Preparação": "Use console e snapshot da VM de laboratório. Identifique distribuição e criptografia antes de alterar o boot.",
                "Recuperação": "Use o modo de recuperação documentado pela distribuição. Em sistemas compatíveis, remonte a raiz para escrita e execute passwd para a conta administrativa.",
                "Finalização": "Restaure a configuração normal de boot e reinicie. Em sistemas SELinux, siga a orientação de relabel da distribuição. Nenhuma etapa é executada por este guia."}


class RestrictedShellReference(Guide):
    PLUGIN_ID = "restricted_shell_reference"
    ALIASES = ("ops:604",)
    NAME = "Referência de shells restritos"
    DESCRIPTION = "Consulta de limitações e superfícies de escape em ambientes de laboratório."
    SECTIONS = {"Inventário": "Identifique comandos permitidos, PATH, editores e interpretadores disponíveis; rbash não é um limite de isolamento do sistema operacional.",
                "Editores": "Editores com execução de comandos, como Vim (:shell), podem ultrapassar uma restrição que permita iniciar o editor.",
                "Interpretadores": "Python, Perl e outros interpretadores permitidos podem iniciar processos. Verifique as políticas do laboratório antes de testar.",
                "Controles": "Compare a restrição de shell com isolamento por contêiner/VM e privilégios efetivos. O guia não executa os exemplos."}


class LegacyARPAgent(BasePlugin):
    PLUGIN_ID = "legacy_arp_agent"
    ALIASES = ("ops:1001",)
    NAME = "Agente ARP legado — lacuna"
    DESCRIPTION = "Registro da opção sem implementação original funcional."
    GROUP = "Misc"
    TACTIC = "Backlog"
    UNAVAILABLE_REASON = "Implementação original ausente; backlog fora da portabilidade."

    def execute(self, p, ctx):
        from core.operations import Unavailable
        raise Unavailable(self.UNAVAILABLE_REASON)
