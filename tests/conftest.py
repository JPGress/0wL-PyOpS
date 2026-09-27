import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def no_external_network(monkeypatch, request):
    if request.node.get_closest_marker("integration"):
        return
    import socket
    import shutil
    original_which = shutil.which
    mock_backends = {"nmap", "exiftool", "smbclient", "rpcclient", "arp-scan", "arpspoof", "tcpdump", "iw", "ip", "airodump-ng", "aireplay-ng", "aircrack-ng", "whois"}
    monkeypatch.setattr(shutil, "which", lambda name: "/fixture/bin/" + name if name in mock_backends else original_which(name))
    def blocked(*args, **kwargs):
        raise AssertionError("Teste unitário tentou acessar rede")
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket.socket, "sendto", blocked)
