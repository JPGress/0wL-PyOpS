"""Validação compartilhada; valores do operador nunca viram opções de shell."""
import argparse
import ipaddress
import re
from urllib.parse import urlsplit


def domain(value):
    value = value.strip().rstrip(".").encode("idna").decode("ascii").lower()
    if len(value) > 253 or not all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", p) for p in value.split(".")):
        raise argparse.ArgumentTypeError("Domínio inválido")
    return value


def host(value):
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return domain(value)


def positive(value):
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Informe um inteiro positivo") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("Informe um inteiro positivo")
    return number


def ports(value):
    result = set()
    try:
        for part in value.split(","):
            pair = part.split("-")
            first, last = int(pair[0]), int(pair[-1])
            if len(pair) > 2 or not 1 <= first <= last <= 65535:
                raise ValueError()
            result.update(range(first, last + 1))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Portas inválidas (ex.: 80,443,8000-8010)") from exc
    return sorted(result)


def url(value):
    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise argparse.ArgumentTypeError("URL HTTP/HTTPS sem credenciais requerida")
    try:
        parsed.port
        host(parsed.hostname)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("URL inválida") from exc
    return value


def targets(value, limit=4096):
    if "/" in value:
        network = ipaddress.ip_network(value, strict=False)
        if network.num_addresses > limit:
            raise ValueError(f"Rede excede o limite de {limit} endereços")
        return [str(ip) for ip in network.hosts()]
    if "-" in value:
        start, end = value.split("-", 1)
        try:
            first, last = ipaddress.ip_address(start), ipaddress.ip_address(end)
        except ValueError:
            return [host(value)]
        if first.version != last.version or not 0 <= int(last) - int(first) < limit:
            raise ValueError("Intervalo inválido ou excessivo")
        return [str(ipaddress.ip_address(n)) for n in range(int(first), int(last) + 1)]
    return [host(value)]
