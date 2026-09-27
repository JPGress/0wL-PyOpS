import ipaddress
import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from core.operations import Context, execute
from plugins.lab import network_lab as lab, wireless


@pytest.fixture
def fake_network(monkeypatch, tmp_path):
    forwarding = tmp_path / "ip_forward"
    forwarding.write_text("0\n")
    monkeypatch.setattr(lab, "FORWARDING", forwarding)
    monkeypatch.setattr(lab, "require_root", lambda: None)
    monkeypatch.setattr(lab, "interface", lambda value: value)
    return forwarding


def test_mitm_restores_after_partial_start(fake_network, monkeypatch, tmp_path):
    first = Mock()
    monkeypatch.setattr(lab, "Process", Mock(side_effect=[first, RuntimeError("fixture failed")]))
    p = lab.ARPMitmLab()
    result = execute(p, dict(interface="lab0", target=ipaddress.IPv4Address("192.0.2.1"), gateway=ipaddress.IPv4Address("192.0.2.2"), duration=1), tmp_path)
    assert fake_network.read_text().strip() == "0"
    first.stop.assert_called_once()
    assert result.status == "partial"
    assert any("fixture failed" in x for x in result.errors)


def test_mitm_cancel_reaps_owned_processes(fake_network, monkeypatch, tmp_path):
    processes = [Mock(), Mock(), Mock()]
    monkeypatch.setattr(lab, "Process", Mock(side_effect=processes))
    monkeypatch.setattr(lab, "wait_processes", Mock(side_effect=KeyboardInterrupt))
    p = lab.ARPMitmLab()
    result = execute(p, dict(interface="lab0", target=ipaddress.IPv4Address("192.0.2.1"), gateway=ipaddress.IPv4Address("192.0.2.2"), duration=1), tmp_path)
    assert result.status == "cancelled"
    assert fake_network.read_text().strip() == "0"
    assert all(proc.stop.call_count == 1 for proc in processes)


def test_route_conflict_no_changes(fake_network, monkeypatch, tmp_path):
    monkeypatch.setattr(lab, "command", lambda *a, **kw: ('[{"dst":"192.0.2.0/24"}]', "", 0))
    p = lab.WSLRoutes()
    result = execute(p, dict(operation="apply", interface="lab0", gateway=ipaddress.IPv4Address("192.0.2.1"), network=[ipaddress.IPv4Network("192.0.2.0/24")]), tmp_path)
    assert "Já existe" in result.errors[0]
    assert fake_network.read_text() == "0\n"


def test_route_rollback(fake_network, monkeypatch, tmp_path):
    calls = []
    existing = []
    def backend(argv, *args, **kwargs):
        calls.append(argv)
        if "-json" in argv:
            return json.dumps(existing), "", 0
        if "add" in argv:
            if "198.51.100.0/24" in argv:
                raise RuntimeError("fixture add failed")
            existing.append(dict(dst="192.0.2.0/24", gateway="192.0.2.1", dev="lab0"))
        return "", "", 0
    monkeypatch.setattr(lab, "command", backend)
    p = lab.WSLRoutes()
    result = execute(p, dict(operation="apply", interface="lab0", gateway=ipaddress.IPv4Address("192.0.2.1"), network=[ipaddress.IPv4Network("192.0.2.0/24"), ipaddress.IPv4Network("198.51.100.0/24")]), tmp_path)
    assert any("del" in x for x in calls)
    assert fake_network.read_text().strip() == "0"
    assert result.status == "partial"


def test_wireless_no_interface_no_changes(monkeypatch, tmp_path):
    monkeypatch.setattr(wireless, "require_root", lambda: None)
    backend = Mock()
    monkeypatch.setattr(wireless, "command", backend)
    p = wireless.WirelessLab()
    params = vars(p.parser().parse_args(["--operation", "capture"]))
    result = execute(p, params, tmp_path)
    assert result.status == "failed"
    backend.assert_not_called()


def test_wireless_capture_cancel_restores(monkeypatch, tmp_path):
    monkeypatch.setattr(wireless, "require_root", lambda: None)
    monkeypatch.setattr(wireless, "interface", lambda x: x)
    calls = []
    def backend(argv, *args, **kw):
        calls.append(argv)
        return ("type managed\nchannel 6 (2437 MHz)" if argv[-1] == "info" else ""), "", 0
    monkeypatch.setattr(wireless, "command", backend)
    proc = Mock()
    monkeypatch.setattr(wireless, "Process", lambda argv: proc)
    monkeypatch.setattr(wireless, "wait_processes", Mock(side_effect=KeyboardInterrupt))
    p = wireless.WirelessLab()
    args = vars(p.parser().parse_args(["--operation", "capture", "--interface", "lab0", "--bssid", "02:00:00:00:00:01", "--channel", "1"]))
    result = execute(p, args, tmp_path)
    assert result.status == "cancelled"
    assert any(x[-1] == "del" for x in calls)
    assert ["iw", "dev", "lab0", "set", "channel", "6"] in calls
    proc.stop.assert_called_once()
