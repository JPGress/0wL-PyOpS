"""Reconhecimento DNS sem dependência do monólito Bash."""
import ipaddress
import json
from pathlib import Path
from plugins.base import BasePlugin
from core.attack import mapping
from core.validation import domain, host, positive, targets
from core.operations import command


def resolver(timeout):
    import dns.resolver
    instance = dns.resolver.Resolver()
    instance.timeout = min(timeout, 5)
    instance.lifetime = timeout
    return instance


def query(name, kind, timeout=10):
    import dns.resolver
    try:
        answer = resolver(timeout).resolve(name, kind)
        return {"name": name, "type": kind, "status": "answer", "values": [str(x) for x in answer]}
    except dns.resolver.NXDOMAIN:
        return {"name": name, "type": kind, "status": "nxdomain", "values": []}
    except dns.resolver.NoAnswer:
        return {"name": name, "type": kind, "status": "no_answer", "values": []}


class DNSBase(BasePlugin):
    GROUP = "Red"
    TACTIC = "TA0043"
    ATTACK = (mapping("T1590.002"),)
    DEPENDENCIES = (("python", "dns"),)

    def add_arguments(self, parser):
        parser.add_argument("--domain", type=domain, required=True)
        parser.add_argument("--timeout", type=positive, default=10)


class DNSRecords(DNSBase):
    PLUGIN_ID = "dns_records"
    ALIASES = ("ops:104",)
    NAME = "Registros DNS"
    DESCRIPTION = "Consulta registros e nomes fornecidos pelo operador."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("--types", nargs="+", choices=("A", "AAAA", "NS", "MX", "TXT", "SOA", "CNAME"), default=["A", "AAAA", "NS", "MX", "TXT", "SOA"])
        parser.add_argument("--names-file", type=Path)

    def execute(self, p, ctx):
        names = [p["domain"]]
        if p.get("names_file"):
            for line in p["names_file"].read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    names.append(domain(line if line.endswith("." + p["domain"]) else line + "." + p["domain"]))
        for name in dict.fromkeys(names):
            for kind in p["types"]:
                try:
                    ctx.finding(**query(name, kind, p["timeout"]))
                except Exception as exc:
                    ctx.error(f"{name}/{kind}: {exc}")


class ReverseDNS(DNSBase):
    PLUGIN_ID = "reverse_dns"
    ALIASES = ("ops:103",)
    NAME = "DNS reverso"
    DESCRIPTION = "Consulta PTR para IP, intervalo ou CIDR (até 4096 endereços)."

    def add_arguments(self, parser):
        parser.add_argument("--target", required=True)
        parser.add_argument("--timeout", type=positive, default=10)

    def execute(self, p, ctx):
        addresses = [ipaddress.ip_address(x) for x in targets(p["target"])]
        for address in addresses:
            try:
                ctx.finding(ip=str(address), **query(address.reverse_pointer, "PTR", p["timeout"]))
            except Exception as exc:
                ctx.error(f"{address}: {exc}")


class CNAMEInventory(DNSBase):
    PLUGIN_ID = "cname_inventory"
    ALIASES = ("ops:202",)
    NAME = "Inventário CNAME"
    DESCRIPTION = "Inventaria aliases DNS; não confirma vulnerabilidade de takeover."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("--names-file", type=Path, required=True)

    def execute(self, p, ctx):
        for line in p["names_file"].read_text().splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            name = domain(line.strip())
            if name != p["domain"] and not name.endswith("." + p["domain"]):
                name = domain(name + "." + p["domain"])
            try:
                result = query(name, "CNAME", p["timeout"])
                result["resolution"] = [query(value, "A", p["timeout"]) for value in result["values"]]
                result["takeover_confirmed"] = False
                ctx.finding(**result)
            except Exception as exc:
                ctx.error(f"{name}: {exc}")


class ZoneTransfer(DNSBase):
    PLUGIN_ID = "dns_zone_transfer"
    ALIASES = ("ops:201",)
    NAME = "Transferência de zona DNS"
    DESCRIPTION = "Consulta AXFR nos servidores autoritativos do domínio informado."

    def execute(self, p, ctx):
        import dns.query
        import dns.zone
        answer = query(p["domain"], "NS", p["timeout"])
        if not answer["values"]:
            ctx.finding(**answer)
            return
        for server in answer["values"]:
            try:
                addresses = query(server, "A", p["timeout"])["values"]
                if not addresses:
                    raise RuntimeError("Servidor sem endereço IPv4")
                transfer = dns.query.xfr(addresses[0], p["domain"], timeout=p["timeout"], lifetime=p["timeout"])
                zone = dns.zone.from_xfr(transfer)
                ctx.finding(server=server, status="transferred", records=zone.to_text().splitlines())
            except Exception as exc:
                ctx.error(f"AXFR {server}: {type(exc).__name__}: {exc}")


class DomainIntelligence(BasePlugin):
    PLUGIN_ID = "domain_intelligence"
    ALIASES = ("ops:102",)
    NAME = "WHOIS e certificados"
    DESCRIPTION = "Consulta WHOIS e transparência de certificados, com fontes distintas."
    GROUP = "Red"
    TACTIC = "TA0043"
    ATTACK = (mapping("T1596.002"), mapping("T1596.003"))
    DEPENDENCIES = (("python", "requests"), ("executable", "whois"))

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--domain", type=domain)
        group.add_argument("--domains-file", type=Path)
        parser.add_argument("--timeout", type=positive, default=20)

    def execute(self, p, ctx):
        import requests
        names = [p["domain"]] if p.get("domain") else [domain(x.strip()) for x in p["domains_file"].read_text().splitlines() if x.strip()]
        for name in dict.fromkeys(names):
            try:
                stdout, _, _ = command(["whois", name], timeout=p["timeout"])
                ctx.finding(domain=name, source="whois", raw=stdout)
            except Exception as exc:
                ctx.error(f"WHOIS {name}: {exc}")
            try:
                response = requests.get("https://crt.sh/", params={"q": "%." + name, "output": "json"}, timeout=p["timeout"])
                response.raise_for_status()
                certificates = response.json()
                if not isinstance(certificates, list):
                    raise ValueError("Resposta CT não é uma lista")
                values = sorted({v for item in certificates for v in item.get("name_value", "").splitlines()})
                ctx.finding(domain=name, source="certificate_transparency", names=values)
            except Exception as exc:
                ctx.error(f"Certificados {name}: {exc}")
