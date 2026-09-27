import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from core.operations import execute
from plugins.recon import dns_tools as dns_tools
from plugins.recon import web_tools as web


def params(plugin, *args):
    return vars(plugin.parser().parse_args(args))


def test_dns_nxdomain_and_empty(monkeypatch):
    import dns.resolver
    fake = Mock()
    monkeypatch.setattr(dns_tools, "resolver", lambda timeout: fake)
    fake.resolve.side_effect = dns.resolver.NXDOMAIN
    assert dns_tools.query("absent.test", "A")["status"] == "nxdomain"
    fake.resolve.side_effect = dns.resolver.NoAnswer
    assert dns_tools.query("empty.test", "AAAA")["status"] == "no_answer"


def test_dns_partial(monkeypatch, tmp_path):
    def query(name, kind, timeout):
        if kind == "AAAA":
            raise TimeoutError("fixture timeout")
        return dict(name=name, type=kind, status="answer", values=["192.0.2.1"])
    monkeypatch.setattr(dns_tools, "query", query)
    plugin = dns_tools.DNSRecords()
    result = execute(plugin, params(plugin, "--domain", "example.test", "--types", "A", "AAAA"), tmp_path)
    assert result.status == "partial"
    assert len(result.findings) == 1
    assert "timeout" in result.errors[0]


def test_cname_not_takeover(monkeypatch, tmp_path):
    names = tmp_path / "names.txt"
    names.write_text("www\n")
    monkeypatch.setattr(dns_tools, "query", lambda name, kind, timeout: dict(name=name, type=kind, status="answer" if kind == "CNAME" else "nxdomain", values=["alias.example.test"] if kind == "CNAME" else []))
    plugin = dns_tools.CNAMEInventory()
    result = execute(plugin, params(plugin, "--domain", "example.test", "--names-file", str(names)), tmp_path)
    assert result.status == "success"
    assert result.findings[0]["takeover_confirmed"] is False
    assert result.findings[0]["resolution"][0]["status"] == "nxdomain"


def test_zone_refused(monkeypatch, tmp_path):
    import dns.query
    monkeypatch.setattr(dns_tools, "query", lambda name, kind, timeout: {"values": ["ns.example.test"] if kind == "NS" else ["192.0.2.1"]})
    monkeypatch.setattr(dns.query, "xfr", Mock(side_effect=RuntimeError("REFUSED")))
    plugin = dns_tools.ZoneTransfer()
    result = execute(plugin, params(plugin, "--domain", "example.test"), tmp_path)
    assert result.status == "partial"
    assert "REFUSED" in result.errors[0]


def test_website_relative_links(monkeypatch, tmp_path):
    monkeypatch.setattr(web, "fetch", lambda *a, **kw: (b'<a href="/doc.pdf">A</a><a href="/doc.pdf">A</a><img src="../x.png"><a href="javascript:void(0)">No</a>', "https://example.test/base/", {}))
    plugin = web.WebsiteInventory()
    result = execute(plugin, params(plugin, "--url", "https://example.test/base/"), tmp_path)
    assert result.status == "success"
    assert {x["url"] for x in result.findings} == {"https://example.test/doc.pdf", "https://example.test/x.png"}


def test_http_blocked(monkeypatch, tmp_path):
    import requests
    response = Mock(url="https://example.test/", status_code=403, headers={"Server": "fixture"}, history=[])
    monkeypatch.setattr(requests, "head", lambda *a, **kw: response)
    plugin = web.HTTPHeaders()
    result = execute(plugin, params(plugin, "--url", "https://example.test", "--context", "external"), tmp_path)
    assert result.status == "partial"
    assert result.attack[0]["technique"] == "T1595"
    response.close.assert_called_once()


def test_http_tls_failure(monkeypatch, tmp_path):
    import requests
    monkeypatch.setattr(requests, "head", Mock(side_effect=requests.exceptions.SSLError("fixture TLS")))
    plugin = web.HTTPHeaders()
    result = execute(plugin, params(plugin, "--url", "https://example.test", "--context", "internal"), tmp_path)
    assert result.status == "failed"
    assert "TLS" in result.errors[0]


def test_metadata_csv_quotes_and_paths(monkeypatch, tmp_path):
    source = tmp_path / "doc with spaces.txt"
    source.write_text("fixture")
    def backend(argv, timeout):
        assert argv[-1] == str(source.resolve())
        return json.dumps([{"Author": 'A, "B"', "Software": "Fixture"}]), "", 0
    monkeypatch.setattr(web, "command", backend)
    plugin = web.DocumentMetadata()
    result = execute(plugin, params(plugin, "--files", str(source)), tmp_path)
    assert result.status == "success"
    csv = next(Path(p) for p in result.artifacts if p.endswith("metadata.csv")).read_text()
    assert '"A, ""B"""' in csv


def test_metadata_bad_json(monkeypatch, tmp_path):
    source = tmp_path / "fixture.txt"
    source.write_text("fixture")
    monkeypatch.setattr(web, "command", lambda *a, **kw: ("not json", "", 0))
    plugin = web.DocumentMetadata()
    result = execute(plugin, params(plugin, "--files", str(source)), tmp_path)
    assert result.status == "partial"
    assert not result.findings


def test_search_blocking_distinct_from_no_results(monkeypatch, tmp_path):
    monkeypatch.setattr(web, "fetch", Mock(side_effect=RuntimeError("403")))
    plugin = web.DocumentMetadata()
    result = execute(plugin, params(plugin, "--domain", "example.test"), tmp_path)
    assert result.status == "partial"
    assert "403" in result.errors[0]
    assert any(p.endswith("search-url.txt") for p in result.artifacts)


def test_whois_and_certificates_distinct_sources(monkeypatch, tmp_path):
    import requests
    monkeypatch.setattr(dns_tools, "command", lambda *a, **kw: ("Domain Name: EXAMPLE.TEST", "", 0))
    response = Mock()
    response.json.return_value = [{"name_value": "www.example.test\nwww.example.test"}]
    monkeypatch.setattr(requests, "get", lambda *a, **kw: response)
    plugin = dns_tools.DomainIntelligence()
    result = execute(plugin, params(plugin, "--domain", "example.test"), tmp_path)
    assert result.status == "success"
    assert [x["source"] for x in result.findings] == ["whois", "certificate_transparency"]
    assert result.findings[1]["names"] == ["www.example.test"]


def test_download_limit(monkeypatch):
    import requests
    response = Mock(url="https://example.test/", headers={})
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.iter_content.return_value = [b"1234", b"5678"]
    monkeypatch.setattr(requests, "get", lambda *a, **kw: response)
    with pytest.raises(ValueError, match="excede"):
        web.fetch("https://example.test/", max_bytes=5)
