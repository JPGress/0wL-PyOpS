"""SMB com perfis explícitos e sem sessões de shell interativas."""
import os
import tempfile
from pathlib import Path
from plugins.base import BasePlugin
from core.attack import mapping
from core.operations import command
from core.validation import host, positive
from plugins.discovery.network import parse_nmap


class SMBInventory(BasePlugin):
    PLUGIN_ID = "smb_inventory"
    ALIASES = ("ops:904",)
    NAME = "Inventário SMB"
    DESCRIPTION = "Enumera serviços e compartilhamentos; perfil de vulnerabilidades opcional."
    GROUP = "Red"
    TACTIC = "TA0007"
    ATTACK = (mapping("T1046", "internal"), mapping("T1135", "internal"), mapping("T1595", "external"), mapping("T1595.002", "external"))
    OPERATION_KEY = "profile"
    OPERATION_DEPENDENCIES = {
        "shares": (("executable", "smbclient"),),
        "rpc": (("executable", "rpcclient"),),
        "services": (("executable", "nmap"),),
        "vulnerabilities": (("executable", "nmap"),),
        "all": (("executable", "smbclient"), ("executable", "rpcclient"), ("executable", "nmap")),
    }

    def add_arguments(self, parser):
        parser.add_argument("--target", type=host, required=True)
        parser.add_argument("--context", choices=("internal", "external"), required=True)
        parser.add_argument("--profile", choices=("shares", "services", "rpc", "vulnerabilities", "all"), default="shares")
        parser.add_argument("--auth-file", type=Path, help="Arquivo Samba username/password/domain com permissão 0600")
        parser.add_argument("--timeout", type=positive, default=60)

    def execute(self, p, ctx):
        if p["context"] == "external":
            ctx.result.attack = [mapping("T1595.002" if p["profile"] == "vulnerabilities" else "T1595", "external")]
        auth = ["-N"]
        if p.get("auth_file"):
            path = p["auth_file"].resolve()
            if not path.is_file() or path.stat().st_mode & 0o077:
                raise ValueError("Arquivo de autenticação deve existir e ser privado (0600)")
            auth = ["-A", str(path)]
        profiles = ["shares", "services", "rpc"] if p["profile"] == "all" else [p["profile"]]
        for profile in profiles:
            try:
                if profile == "shares":
                    argv = ["smbclient", "-g", "-L", "//" + p["target"], *auth]
                elif profile == "rpc":
                    argv = ["rpcclient", *auth, "-c", "srvinfo;netshareenumall", p["target"]]
                else:
                    path = ctx.artifact(profile + ".xml")
                    scripts = "smb-os-discovery,smb-protocols" if profile == "services" else "smb-vuln-ms17-010"
                    argv = ["nmap", "-sT", "-p", "139,445", "--script", scripts, "-oX", str(path), p["target"]]
                stdout, stderr, code = command(argv, p["timeout"], check=False)
                ctx.artifact(profile + ".txt", stdout + "\n" + stderr)
                if code:
                    ctx.error(f"{profile}: retorno {code}; {stderr[:1000]}")
                ctx.finding(profile=profile, status="success" if code == 0 else "failed", returncode=code,
                            output=stdout)
                if profile in ("services", "vulnerabilities") and path.exists():
                    for item in parse_nmap(path.read_text()):
                        ctx.finding(profile=profile, **item)
            except Exception as exc:
                ctx.error(f"{profile}: {exc}")
