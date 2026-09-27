"""Execução parametrizada, artefatos e processos pertencentes à operação."""
import json
import os
import signal
import subprocess
import tempfile
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


class Unavailable(RuntimeError):
    pass


@dataclass
class Result:
    plugin_id: str
    status: str = "success"
    schema_version: int = 1
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: str = ""
    parameters: dict = field(default_factory=dict)
    findings: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    artifacts: list = field(default_factory=list)
    attack: list = field(default_factory=list)


class Context:
    def __init__(self, plugin_id, parameters, output_dir="outputs"):
        self.result = Result(plugin_id=plugin_id, parameters={
            k: json.loads(json.dumps(v, default=str)) for k, v in parameters.items()
            if not any(word in k.lower() for word in ("password", "secret", "token"))
        })
        self.directory = Path(output_dir) / plugin_id / uuid.uuid4().hex

    def path(self, name):
        if Path(name).name != name:
            raise ValueError("Nome de artefato inválido")
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        return self.directory / name

    def artifact(self, name, content=None):
        path = self.path(name)
        if content is not None:
            with path.open("xb") as stream:
                stream.write(content if isinstance(content, bytes) else content.encode("utf-8"))
            path.chmod(0o600)
        value = str(path.resolve())
        if value not in self.result.artifacts:
            self.result.artifacts.append(value)
        return path

    def finding(self, **values):
        self.result.findings.append(values)

    def error(self, message):
        self.result.errors.append(str(message))
        self.result.status = "partial"

    def finish(self):
        self.result.finished_at = datetime.now(timezone.utc).isoformat()
        path = self.artifact("result.json")
        with path.open("x", encoding="utf-8") as stream:
            self.result.artifacts = [item for item in self.result.artifacts if Path(item).is_file()]
            json.dump(asdict(self.result), stream, ensure_ascii=False, indent=2)
        for artifact in self.result.artifacts:
            if Path(artifact).is_file():
                Path(artifact).chmod(0o600)
        return self.result


class Process:
    """Nunca usa shell; cancela apenas o grupo criado por esta instância."""
    def __init__(self, argv):
        self.stdout = tempfile.TemporaryFile()
        self.stderr = tempfile.TemporaryFile()
        self.collected = None
        try:
            self.process = subprocess.Popen(
                [str(arg) for arg in argv], stdin=subprocess.DEVNULL,
                stdout=self.stdout, stderr=self.stderr,
                start_new_session=True,
            )
        except OSError as exc:
            self.stdout.close()
            self.stderr.close()
            raise Unavailable(f"Executável indisponível: {argv[0]}: {exc}") from exc

    def stop(self):
        try:
            os.killpg(self.process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        if self.process.poll() is None:
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait()

    def collect(self, timeout=30, check=True):
        if self.collected is not None:
            return self.collected
        try:
            self.process.wait(timeout=timeout)
        except BaseException:
            self.stop()
            self.stdout.close()
            self.stderr.close()
            raise
        self.stdout.seek(0)
        self.stderr.seek(0)
        limit = 16 * 1024 * 1024
        stdout, stderr = self.stdout.read(limit + 1), self.stderr.read(limit + 1)
        self.stdout.close()
        self.stderr.close()
        if len(stdout) > limit or len(stderr) > limit:
            raise RuntimeError("Saída do backend excedeu 16 MiB; use um artefato dedicado")
        self.collected = (stdout.decode(errors="replace"), stderr.decode(errors="replace"), self.process.returncode)
        if check and self.process.returncode:
            raise RuntimeError(f"Backend retornou {self.process.returncode}: {stderr.decode(errors='replace')[:2000]}")
        return self.collected


def command(argv, timeout=30, check=True):
    return Process(argv).collect(timeout, check)


EXIT_CODES = {"success": 0, "failed": 1, "unavailable": 3, "partial": 4, "cancelled": 130}


def execute(plugin, parameters, output_dir="outputs"):
    context = Context(plugin.PLUGIN_ID, parameters, output_dir)
    context.result.attack = [m for m in plugin.ATTACK
                             if not m.get("context") or m["context"] == parameters.get("context")]
    previous_sigterm = None
    if threading.current_thread() is threading.main_thread():
        previous_sigterm = signal.getsignal(signal.SIGTERM)
        def cancelled(signum, frame):
            raise KeyboardInterrupt()
        signal.signal(signal.SIGTERM, cancelled)
    try:
        missing = plugin.unavailable(parameters)
        if missing:
            raise Unavailable("; ".join(missing))
        plugin.execute(parameters, context)
    except Unavailable as exc:
        context.result.status = "unavailable"
        context.result.errors.append(str(exc))
    except (KeyboardInterrupt, EOFError):
        context.result.status = "cancelled"
    except Exception as exc:
        context.result.status = "partial" if context.result.findings else "failed"
        context.result.errors.append(str(exc))
    finally:
        if previous_sigterm is not None:
            signal.signal(signal.SIGTERM, previous_sigterm)
    try:
        return context.finish()
    except OSError as exc:
        context.result.errors.append(f"Não foi possível gravar relatório: {exc}")
        context.result.status = "partial" if context.result.findings else "failed"
        return context.result
