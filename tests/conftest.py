import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def no_external_network(monkeypatch, request):
    if request.node.get_closest_marker("integration"):
        return
    import socket
    def blocked(*args, **kwargs):
        raise AssertionError("Teste unitário tentou acessar rede")
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket.socket, "sendto", blocked)
