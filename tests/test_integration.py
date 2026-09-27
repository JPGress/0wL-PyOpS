"""Integrações somente loopback e arquivos sintéticos. Opt-in: -m integration."""
import json
import shutil
import socket
import socketserver
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import pytest
from core.operations import execute
from plugins.discovery.network import TCPScan, NmapScan
from plugins.recon.web_tools import HTTPHeaders, DocumentMetadata, WebsiteInventory
from plugins.recon.dns_tools import DNSRecords, ReverseDNS

pytestmark = pytest.mark.integration


@pytest.fixture
def http_lab():
    class Handler(BaseHTTPRequestHandler):
        def do_HEAD(self):
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "/")
            else:
                self.send_response(200)
                self.send_header("X-Fixture", "owl-test")
            self.end_headers()
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b'<a href="/fixture.pdf">fixture</a>')
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def run(plugin, tmp_path, args):
    return execute(plugin, vars(plugin.parser().parse_args(args)), tmp_path)


def test_tcp_loopback_open(http_lab, tmp_path):
    result = run(TCPScan(), tmp_path, ["--target", "127.0.0.1", "--ports", str(http_lab), "--context", "internal"])
    assert result.status == "success"
    assert result.findings[0]["status"] == "open"


def test_http_loopback_redirect(http_lab, tmp_path):
    result = run(HTTPHeaders(), tmp_path, ["--url", f"http://127.0.0.1:{http_lab}/redirect", "--context", "internal"])
    assert result.status == "success"
    assert result.findings[0]["headers"]["X-Fixture"] == "owl-test"
    assert result.findings[0]["redirects"][0]["status"] == 302


def test_website_loopback(http_lab, tmp_path):
    result = run(WebsiteInventory(), tmp_path, ["--url", f"http://127.0.0.1:{http_lab}/"])
    assert result.status == "success"
    assert result.findings[0]["url"].endswith("/fixture.pdf")


@pytest.mark.skipif(not shutil.which("nmap"), reason="Nmap ausente")
def test_nmap_loopback(http_lab, tmp_path):
    result = run(NmapScan(), tmp_path, ["--target", "127.0.0.1", "--ports", str(http_lab), "--context", "internal"])
    assert result.status == "success", result.errors
    assert result.findings[0]["state"] == "open"
    assert Path(next(p for p in result.artifacts if p.endswith("nmap.xml"))).is_file()


@pytest.mark.skipif(not shutil.which("exiftool"), reason="ExifTool ausente")
def test_exiftool_synthetic_document(tmp_path):
    document = tmp_path / "synthetic.txt"
    document.write_text("Synthetic document for local integration.\n")
    result = run(DocumentMetadata(), tmp_path / "output", ["--files", str(document)])
    assert result.status == "success", result.errors
    assert result.findings[0]["metadata"]["FileType"] == "TXT"


def test_dns_loopback(monkeypatch, tmp_path):
    import dns.message
    import dns.rrset
    import dns.resolver
    from plugins.recon import dns_tools
    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            wire, sock = self.request
            request = dns.message.from_wire(wire)
            response = dns.message.make_response(request)
            question = request.question[0]
            kind = dns.rdatatype.to_text(question.rdtype)
            value = "192.0.2.1" if kind == "A" else "host.example.test."
            response.answer.append(dns.rrset.from_text(str(question.name), 60, "IN", kind, value))
            sock.sendto(response.to_wire(), self.client_address)
    server = socketserver.UDPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def resolver(timeout):
        instance = dns.resolver.Resolver(configure=False)
        instance.nameservers = ["127.0.0.1"]
        instance.port = server.server_address[1]
        instance.lifetime = timeout
        return instance
    monkeypatch.setattr(dns_tools, "resolver", resolver)
    try:
        result = run(DNSRecords(), tmp_path, ["--domain", "example.test", "--types", "A"])
        assert result.status == "success", result.errors
        assert result.findings[0]["values"] == ["192.0.2.1"]
        reverse = run(ReverseDNS(), tmp_path, ["--target", "192.0.2.1"])
        assert reverse.findings[0]["values"] == ["host.example.test."]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
