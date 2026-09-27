import json
import argparse
import subprocess
import sys
from pathlib import Path
import pytest
from core.attack import validate
from core.cli import main
from core.operations import Context, Process, execute
from core.registry import PluginRegistry
from core.validation import domain, host, ports, targets, url
from plugins import load_plugins
from plugins.base import BasePlugin
from plugins.recon.web_tools import SearchQueries


class Synthetic(BasePlugin):
    PLUGIN_ID = "synthetic"
    NAME = "Synthetic"
    GROUP = "Misc"
    TACTIC = "Test"
    DESCRIPTION = "Fixture sintética"

    def execute(self, p, ctx):
        ctx.finding(value="before")
        if p.get("fail"):
            raise RuntimeError("failure")
        if p.get("cancel"):
            raise KeyboardInterrupt()


def register(registry, plugin):
    registry.register(plugin.PLUGIN_ID, plugin.NAME, plugin.GROUP, plugin.TACTIC,
                      plugin.DESCRIPTION, plugin.run, plugin)


def test_collision_is_atomic():
    registry = PluginRegistry()
    plugin = Synthetic()
    plugin.ALIASES = ("old",)
    register(registry, plugin)
    second = Synthetic()
    second.PLUGIN_ID = "other"
    second.ALIASES = ("old",)
    with pytest.raises(ValueError, match="Colisão"):
        register(registry, second)
    assert list(registry.plugins) == ["synthetic"]
    assert registry.get_plugin("old")["instance"] is plugin
    assert len(registry.groups["Misc"]["Test"]) == 1


def test_loader_idempotent_and_full_legacy_catalog():
    registry = load_plugins()
    assert not registry.errors
    count = len(registry.plugins)
    assert load_plugins() is registry
    assert len(registry.plugins) == count
    old = [*range(101, 107), 201, 202, 301, *range(601, 605), 801,
           *range(901, 910), 1001]
    for number in old:
        assert registry.get_plugin(f"ops:{number}"), number
    for number in ("001", "002", "003"):
        assert registry.get_plugin("ops:" + number)
    assert registry.get_plugin("001")["id"] == "tcp_scan"
    for existing in ("043", "080", "tcp_rev_shell"):
        assert registry.get_plugin(existing)


def test_loader_reports_broken_module(monkeypatch):
    import plugins
    original = plugins.importlib.import_module
    def wrapped(name):
        if name == "plugins.recon.dns_tools":
            raise ImportError("synthetic missing")
        return original(name)
    monkeypatch.setattr(plugins.importlib, "import_module", wrapped)
    assert any("synthetic missing" in x for x in load_plugins().errors)


def test_invalid_attack_relation():
    p = Synthetic()
    p.ATTACK = ({"tactic": "TA0007", "technique": "T1594"},)
    with pytest.raises(ValueError):
        validate(p)


@pytest.mark.parametrize("params,status", [({}, "success"), ({"fail": True}, "partial"), ({"cancel": True}, "cancelled")])
def test_results_survive_errors(tmp_path, params, status):
    result = execute(Synthetic(), params, tmp_path)
    assert result.status == status
    report = Path(result.artifacts[-1])
    persisted = json.loads(report.read_text())
    assert persisted["artifacts"] == result.artifacts
    assert persisted["findings"] == [{"value": "before"}]
    assert report.stat().st_mode & 0o077 == 0


def test_missing_dependency_not_success(tmp_path, monkeypatch):
    p = Synthetic()
    p.DEPENDENCIES = (("executable", "nonexistent-owl-fixture"),)
    result = execute(p, {}, tmp_path)
    assert result.status == "unavailable"
    assert not result.findings


def test_paths_serialized_and_secrets_omitted(tmp_path):
    result = execute(Synthetic(), {"path": tmp_path, "password": "not-logged"}, tmp_path)
    assert result.parameters == {"path": str(tmp_path)}
    assert "not-logged" not in Path(result.artifacts[-1]).read_text()


def test_artifact_path_traversal(tmp_path):
    ctx = Context("test", {}, tmp_path)
    with pytest.raises(ValueError):
        ctx.artifact("../outside", "bad")


def test_cli_json_alias_and_no_prompt(tmp_path, capsys):
    code = main(["run", "ops:105", "--query", "fixture & value", "--format", "json", "--output-dir", str(tmp_path)])
    output = json.loads(capsys.readouterr().out)
    assert code == 0
    assert output["plugin_id"] == "search_queries"
    assert "fixture+%26+value" in output["findings"][0]["url"]


def test_cli_invalid_args(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["run", "tcp_scan", "--ports", "0", "--target", "127.0.0.1", "--context", "internal"])
    assert exc.value.code == 2


def test_cli_legacy_noninteractive(capsys):
    assert main(["run", "tcp_rev_shell"]) == 3
    assert "somente" in capsys.readouterr().err


def test_matrix_no_fake_ready(capsys):
    assert main(["matrix", "--format", "json"]) == 0
    matrix = json.loads(capsys.readouterr().out)
    assert matrix["attack_version"] == "19.2"
    assert any(x["state"] == "gap" for x in matrix["rows"])
    assert all(not x["validated"] for x in matrix["rows"] if x["kind"] == "reference")
    assert {"TA0005", "TA0112"} <= {x["tactic"] for x in matrix["rows"]}


@pytest.mark.parametrize("value", ["-oX", "name;evil", "", "a..b", "x/../../y"])
def test_reject_invalid_hosts(value):
    with pytest.raises((ValueError, argparse.ArgumentTypeError)):
        host(value)


def test_validation():
    assert ports("80,443,80,8000-8001") == [80, 443, 8000, 8001]
    assert domain("EXAMPLE.TEST.") == "example.test"
    assert targets("192.0.2.1-192.0.2.3") == ["192.0.2.1", "192.0.2.2", "192.0.2.3"]
    with pytest.raises(ValueError):
        targets("0.0.0.0/0")
    with pytest.raises(argparse.ArgumentTypeError):
        url("https://name:password@example.test/")


def test_command_literal_arguments():
    from core.operations import command
    token = "$(touch SHOULD_NOT_EXIST); spaces"
    stdout, _, code = command([sys.executable, "-c", "import sys; print(sys.argv[1])", token])
    assert stdout.strip() == token
    assert code == 0
    assert not Path("SHOULD_NOT_EXIST").exists()


def test_process_timeout_reaps_child():
    process = Process([sys.executable, "-c", "import time; time.sleep(20)"])
    with pytest.raises(subprocess.TimeoutExpired):
        process.collect(timeout=0.05)
    assert process.process.poll() is not None


def test_backend_nonzero():
    from core.operations import command
    with pytest.raises(RuntimeError, match="7"):
        command([sys.executable, "-c", "import sys; sys.stderr.write('fixture'); sys.exit(7)"])


def test_large_backend_output():
    from core.operations import command
    stdout, _, _ = command([sys.executable, "-c", "print('x' * 1000000)"])
    assert len(stdout) == 1000001
