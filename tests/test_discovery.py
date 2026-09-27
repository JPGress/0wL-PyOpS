import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from core.operations import Context, execute
from plugins.discovery import network, local, smb


def params(plugin, *args):
    return vars(plugin.parser().parse_args(args))


def test_nmap_xml():
    xml = '<nmaprun><host><address addr="192.0.2.1"/><ports><port portid="443" protocol="tcp"><state state="open"/><service name="https"/><script id="fixture" output="value"/></port></ports></host></nmaprun>'
    data = list(network.parse_nmap(xml))
    assert data[0]["port"] == 443
    assert data[0]["service"]["name"] == "https"
    assert data[0]["scripts"][0]["id"] == "fixture"
    with pytest.raises(Exception):
        list(network.parse_nmap("not xml"))


def test_nmap_backend_argv_and_artifact(tmp_path, monkeypatch):
    def backend(argv, timeout):
        assert argv[-1] == "192.0.2.1"
        assert argv[argv.index("-p") + 1] == "80,443"
        Path(argv[argv.index("-oX") + 1]).write_text('<nmaprun><host><address addr="192.0.2.1"/><ports><port portid="80" protocol="tcp"><state state="open"/></port></ports></host></nmaprun>')
        return "", "", 0
    monkeypatch.setattr(network, "command", backend)
    p = network.NmapScan()
    result = execute(p, params(p, "--target", "192.0.2.1", "--ports", "80,443", "--context", "internal"), tmp_path)
    assert result.status == "success"
    assert result.attack[0]["technique"] == "T1046"
    assert any(x.endswith("nmap.xml") for x in result.artifacts)


def test_tcp_failure_not_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(network.socket, "create_connection", Mock(side_effect=OSError("no route")))
    p = network.TCPScan()
    result = execute(p, params(p, "--target", "192.0.2.1", "--ports", "80", "--context", "external"), tmp_path)
    assert result.status == "partial"
    assert result.findings[0]["status"] == "error"


@pytest.mark.parametrize("error,state", [(ConnectionRefusedError(), "closed"), (TimeoutError(), "timeout")])
def test_tcp_states(monkeypatch, error, state):
    monkeypatch.setattr(network.socket, "create_connection", Mock(side_effect=error))
    assert network.probe("192.0.2.1", 80, 1)["status"] == state


def test_filesystem_synthetic_permissions_and_symlink(tmp_path):
    root = tmp_path / "tree"
    root.mkdir()
    secret = root / "id_rsa"
    secret.write_text("synthetic-private-content")
    secret.chmod(0o666)
    (root / "loop").symlink_to(root, target_is_directory=True)
    p = local.FilesystemAudit()
    result = execute(p, params(p, "--roots", str(root)), tmp_path / "output")
    assert result.status == "success"
    assert result.findings[0]["indicators"] == ["world_writable", "sensitive_filename"]
    assert "synthetic-private-content" not in json.dumps(result.findings)
    assert result.findings[-1]["entries_inspected"] < 10


def test_filesystem_limit_is_partial(tmp_path):
    root = tmp_path / "tree"
    root.mkdir()
    for index in range(3):
        (root / f"file{index}").touch()
    p = local.FilesystemAudit()
    result = execute(p, params(p, "--roots", str(root), "--max-entries", "1"), tmp_path / "output")
    assert result.status == "partial"


def test_smb_denied_not_success(tmp_path, monkeypatch):
    monkeypatch.setattr(smb, "command", lambda *a, **kw: ("", "NT_STATUS_ACCESS_DENIED", 1))
    p = smb.SMBInventory()
    result = execute(p, params(p, "--target", "192.0.2.1", "--context", "internal"), tmp_path)
    assert result.status == "partial"
    assert result.findings[0]["status"] == "failed"
    assert "ACCESS_DENIED" in result.errors[0]


def test_smb_no_implicit_vulnerability_scan(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(smb, "command", lambda argv, *a, **kw: (calls.append(argv) or "Disk|fixture|", "", 0))
    p = smb.SMBInventory()
    result = execute(p, params(p, "--target", "192.0.2.1", "--context", "internal"), tmp_path)
    assert result.status == "success"
    assert calls == [["smbclient", "-g", "-L", "//192.0.2.1", "-N"]]


def test_smb_private_auth_required(tmp_path):
    auth = tmp_path / "auth"
    auth.write_text("username=fixture\npassword=fixture")
    auth.chmod(0o644)
    p = smb.SMBInventory()
    result = execute(p, params(p, "--target", "192.0.2.1", "--context", "internal", "--auth-file", str(auth)), tmp_path)
    assert result.status == "failed"
    assert "privado" in result.errors[0]
