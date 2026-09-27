"""Motores de descoberta de rede."""
import concurrent.futures
import ipaddress
import socket
import xml.etree.ElementTree as ET
from plugins.base import BasePlugin
from core.attack import mapping
from core.validation import host, ports, positive, targets
from core.operations import command


class NetworkBase(BasePlugin):
    GROUP = "Red"
    TACTIC = "TA0007"
    ATTACK = (mapping("T1046", "internal"), mapping("T1595", "external"))

    def add_arguments(self, parser):
        parser.add_argument("--target", required=True)
        parser.add_argument("--ports", type=ports, required=True)
        parser.add_argument("--context", choices=("internal", "external"), required=True)
        parser.add_argument("--timeout", type=positive, default=3)


def probe(target, port, timeout):
    try:
        with socket.create_connection((target, port), timeout=timeout):
            return {"host": target, "port": port, "status": "open"}
    except ConnectionRefusedError:
        return {"host": target, "port": port, "status": "closed"}
    except (TimeoutError, socket.timeout):
        return {"host": target, "port": port, "status": "timeout"}
    except OSError as exc:
        return {"host": target, "port": port, "status": "error", "error": str(exc)}


class TCPScan(NetworkBase):
    PLUGIN_ID = "tcp_scan"
    ALIASES = ("ops:901", "ops:902", "001")
    NAME = "Scanner TCP"
    DESCRIPTION = "Conexões TCP com concorrência limitada e resultado por porta."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("--workers", type=positive, default=16)

    def execute(self, p, ctx):
        hosts = targets(p["target"])
        if len(hosts) * len(p["ports"]) > 65536 or p["workers"] > 128:
            raise ValueError("Limite: 65536 pares host/porta e 128 workers")
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=p["workers"])
        pending = set()
        jobs = iter((target, port) for target in hosts for port in p["ports"])
        try:
            while True:
                while len(pending) < p["workers"] * 2:
                    pair = next(jobs, None)
                    if pair is None:
                        break
                    pending.add(pool.submit(probe, *pair, p["timeout"]))
                if not pending:
                    break
                done, pending = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
                for task in done:
                    result = task.result()
                    ctx.finding(**result)
                    if result["status"] == "error":
                        ctx.error(f"{result['host']}:{result['port']}: {result['error']}")
        finally:
            for task in pending:
                task.cancel()
            pool.shutdown(wait=True, cancel_futures=True)


def parse_nmap(xml):
    root = ET.fromstring(xml)
    for entry in root.findall("host"):
        address = entry.find("address")
        for port in entry.findall("ports/port"):
            state = port.find("state")
            service = port.find("service")
            yield {"host": address.get("addr") if address is not None else "",
                   "port": int(port.get("portid")), "protocol": port.get("protocol"),
                   "state": state.get("state") if state is not None else "unknown",
                   "service": dict(service.attrib) if service is not None else {},
                   "scripts": [dict(x.attrib) for x in port.findall("script")]}


class NmapScan(NetworkBase):
    PLUGIN_ID = "nmap_scan"
    ALIASES = ("ops:908",)
    NAME = "Nmap"
    DESCRIPTION = "Executa Nmap e preserva o XML original."
    DEPENDENCIES = (("executable", "nmap"),)

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.set_defaults(timeout=300)
        parser.add_argument("--service-detection", action="store_true")

    def execute(self, p, ctx):
        hosts = targets(p["target"])
        path = ctx.artifact("nmap.xml")
        argv = ["nmap", "-sT", "-p", ",".join(map(str, p["ports"])), "-oX", str(path)]
        if p["service_detection"]:
            argv.append("-sV")
        command(argv + hosts, timeout=p["timeout"])
        for item in parse_nmap(path.read_text()):
            ctx.finding(**item)


class ARPDiscovery(BasePlugin):
    PLUGIN_ID = "arp_discovery"
    ALIASES = ("ops:909",)
    NAME = "Descoberta ARP"
    DESCRIPTION = "Descobre vizinhos com arp-scan em uma interface explícita."
    GROUP = "Red"
    TACTIC = "TA0007"
    ATTACK = (mapping("T1018"),)
    DEPENDENCIES = (("executable", "arp-scan"),)

    def add_arguments(self, parser):
        parser.add_argument("--interface", required=True)
        parser.add_argument("--network", required=True)
        parser.add_argument("--timeout", type=positive, default=60)

    def execute(self, p, ctx):
        network = ipaddress.IPv4Network(p["network"], strict=False)
        if p["interface"] not in dict((name, n) for n, name in socket.if_nameindex()):
            raise ValueError("Interface não encontrada")
        stdout, _, _ = command(["arp-scan", "--interface=" + p["interface"], str(network)], p["timeout"])
        ctx.artifact("arp.txt", stdout)
        for line in stdout.splitlines():
            fields = line.split("\t")
            try:
                ipaddress.IPv4Address(fields[0])
            except ValueError:
                continue
            if len(fields) >= 2:
                ctx.finding(ip=fields[0], mac=fields[1], vendor=" ".join(fields[2:]))
