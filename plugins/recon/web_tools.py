"""HTTP, inventário de sites, consultas e metadados documentais."""
import csv
import io
import json
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlencode
import webbrowser
from plugins.base import BasePlugin
from core.attack import mapping
from core.validation import url, domain, positive
from core.operations import command


def fetch(address, timeout=15, max_bytes=10 * 1024 * 1024):
    import requests
    with requests.get(address, timeout=timeout, stream=True) as response:
        response.raise_for_status()
        chunks, size = [], 0
        for chunk in response.iter_content(65536):
            size += len(chunk)
            if size > max_bytes:
                raise ValueError(f"Download excede {max_bytes} bytes")
            chunks.append(chunk)
        return b"".join(chunks), response.url, dict(response.headers)


class HTTPHeaders(BasePlugin):
    PLUGIN_ID = "http_headers"
    ALIASES = ("ops:903",)
    NAME = "Cabeçalhos HTTP"
    DESCRIPTION = "Coleta cabeçalhos, status e redirecionamentos com TLS validado."
    GROUP = "Red"
    TACTIC = "TA0007"
    ATTACK = (mapping("T1046", "internal"), mapping("T1595", "external"))
    DEPENDENCIES = (("python", "requests"),)

    def add_arguments(self, parser):
        parser.add_argument("--url", type=url, required=True)
        parser.add_argument("--context", choices=("internal", "external"), required=True)
        parser.add_argument("--timeout", type=positive, default=15)

    def execute(self, p, ctx):
        import requests
        response = requests.head(p["url"], timeout=p["timeout"], allow_redirects=True)
        try:
            ctx.finding(url=response.url, status_code=response.status_code,
                        headers=dict(response.headers),
                        redirects=[{"url": r.url, "status": r.status_code} for r in response.history])
            if response.status_code >= 400:
                ctx.error(f"HTTP {response.status_code}")
        finally:
            response.close()


class WebsiteInventory(BasePlugin):
    PLUGIN_ID = "website_inventory"
    ALIASES = ("ops:106",)
    NAME = "Inventário de site"
    DESCRIPTION = "Extrai links de uma página e enriquece hosts selecionados com DNS/WHOIS."
    GROUP = "Red"
    TACTIC = "TA0043"
    ATTACK = (mapping("T1594"), mapping("T1590.002"), mapping("T1596.002"))
    DEPENDENCIES = (("python", "requests"), ("python", "bs4"))

    def add_arguments(self, parser):
        parser.add_argument("--url", type=url, required=True)
        parser.add_argument("--timeout", type=positive, default=15)
        parser.add_argument("--enrich", nargs="*", type=domain, default=[])

    def execute(self, p, ctx):
        from bs4 import BeautifulSoup
        data, final_url, _ = fetch(p["url"], p["timeout"])
        soup = BeautifulSoup(data, "html.parser")
        links = set()
        for element in soup.find_all(href=True) + soup.find_all(src=True):
            value = urljoin(final_url, element.get("href") or element.get("src"))
            if urlsplit(value).scheme in ("http", "https"):
                links.add(value)
        for value in sorted(links):
            ctx.finding(url=value, host=urlsplit(value).hostname, source=final_url)
        from plugins.recon.dns_tools import query
        for name in p["enrich"]:
            try:
                ctx.finding(**query(name, "A", p["timeout"]))
            except Exception as exc:
                ctx.error(f"DNS {name}: {exc}")
            try:
                raw, _, _ = command(["whois", name], p["timeout"])
                ctx.finding(host=name, source="whois", raw=raw)
            except Exception as exc:
                ctx.error(f"WHOIS {name}: {exc}")


class SearchQueries(BasePlugin):
    PLUGIN_ID = "search_queries"
    ALIASES = ("ops:105",)
    NAME = "Consultas de reconhecimento"
    DESCRIPTION = "Gera URLs de consultas; abre navegador somente com --open-browser."
    GROUP = "Red"
    TACTIC = "TA0043"
    ATTACK = (mapping("T1593.002"),)

    def add_arguments(self, parser):
        parser.add_argument("--query", required=True)
        parser.add_argument("--site", action="append", type=domain, default=[])
        parser.add_argument("--filetype", action="append", choices=("pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv"), default=[])
        parser.add_argument("--open-browser", action="store_true")

    def execute(self, p, ctx):
        queries = [p["query"]]
        queries.extend(f"{p['query']} site:{site}" for site in p["site"])
        queries.extend(f"{p['query']} filetype:{kind}" for kind in p["filetype"])
        for query in queries:
            address = "https://www.google.com/search?" + urlencode({"q": query})
            ctx.finding(query=query, url=address, status="query_generated")
            if p["open_browser"] and not webbrowser.open(address):
                ctx.error("Não foi possível abrir navegador")
        ctx.artifact("queries.txt", "\n".join(f["url"] for f in ctx.result.findings))


class DocumentMetadata(BasePlugin):
    PLUGIN_ID = "document_metadata"
    ALIASES = ("ops:101",)
    NAME = "Metadados de documentos"
    DESCRIPTION = "Descobre/importa documentos, extrai metadados e exporta JSON/CSV."
    GROUP = "Red"
    TACTIC = "TA0043"
    ATTACK = (mapping("T1589"), mapping("T1592.002"))
    DEPENDENCIES = (("executable", "exiftool"), ("python", "requests"), ("python", "bs4"))

    def add_arguments(self, parser):
        parser.add_argument("--files", nargs="+", type=Path, default=[])
        parser.add_argument("--urls-file", type=Path)
        parser.add_argument("--url", type=url, action="append", default=[])
        parser.add_argument("--domain", type=domain)
        parser.add_argument("--timeout", type=positive, default=30)
        parser.add_argument("--max-documents", type=positive, default=20)

    def execute(self, p, ctx):
        from bs4 import BeautifulSoup
        files = list(p["files"])
        addresses = list(p["url"])
        if p.get("urls_file"):
            addresses.extend(url(line.strip()) for line in p["urls_file"].read_text().splitlines() if line.strip())
        if p.get("domain"):
            search = "https://www.google.com/search?" + urlencode({"q": f"site:{p['domain']} filetype:pdf"})
            ctx.artifact("search-url.txt", search)
            try:
                body, _, _ = fetch(search, p["timeout"])
                for item in BeautifulSoup(body, "html.parser").find_all("a", href=True):
                    link = item["href"]
                    if link.startswith("/url?"):
                        from urllib.parse import parse_qs
                        link = parse_qs(urlsplit(link).query).get("q", [""])[0]
                    parsed = urlsplit(link)
                    if parsed.scheme in ("http", "https") and (parsed.hostname == p["domain"] or (parsed.hostname or "").endswith("." + p["domain"])) and parsed.path.lower().endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx")):
                        addresses.append(link)
                if not addresses:
                    ctx.error("Busca sem documentos extraíveis: resultado vazio ou bloqueio. Use URLs/arquivos próprios; consulte search-url.txt.")
            except Exception as exc:
                ctx.error(f"Busca: {exc}; use URLs/arquivos próprios")
        if not files and not addresses and not p.get("domain"):
            raise ValueError("Informe --files, --url, --urls-file ou --domain")
        for index, address in enumerate(dict.fromkeys(addresses)):
            if len(files) >= p["max_documents"]:
                ctx.error("Limite de documentos alcançado")
                break
            try:
                body, _, _ = fetch(url(address), p["timeout"], 25 * 1024 * 1024)
                path = ctx.artifact(f"document-{index}.bin", body)
                files.append(path)
            except Exception as exc:
                ctx.error(f"Download {address}: {exc}")
        summary = io.StringIO()
        writer = csv.writer(summary)
        writer.writerow(["File", "Field", "Value"])
        for path in files[:p["max_documents"]]:
            try:
                if not path.is_file():
                    raise ValueError("Arquivo não encontrado")
                raw, _, _ = command(["exiftool", "-json", str(path.resolve())], p["timeout"])
                records = json.loads(raw)
                if not isinstance(records, list):
                    raise ValueError("Resposta ExifTool inválida")
                for record in records:
                    ctx.finding(file=str(path), metadata=record)
                    for key in ("Author", "Creator", "CreatorTool", "Producer", "Software", "MIMEType", "CreateDate", "ModifyDate"):
                        if key in record:
                            writer.writerow([str(path), key, record[key]])
            except Exception as exc:
                ctx.error(f"Metadados {path}: {exc}")
        ctx.artifact("metadata.csv", summary.getvalue())
