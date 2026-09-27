"""Inventário local e auditoria de metadados do filesystem."""
import os
import platform
import pwd
import grp
import stat
from pathlib import Path
from plugins.base import BasePlugin
from core.attack import mapping
from core.validation import positive
from core.operations import command


def inventory(ctx):
    ctx.finding(section="system", system=platform.system(), release=platform.release(),
                machine=platform.machine(), hostname=platform.node(), uid=os.getuid(), groups=os.getgroups())
    for filename in ("/etc/os-release", "/proc/version", "/proc/meminfo", "/proc/net/arp", "/etc/resolv.conf"):
        try:
            ctx.finding(section="system", path=filename, content=Path(filename).read_text()[:32768])
        except OSError as exc:
            ctx.error(f"{filename}: {exc}")
    ctx.finding(section="accounts", users=[{"name": x.pw_name, "uid": x.pw_uid, "gid": x.pw_gid, "shell": x.pw_shell} for x in pwd.getpwall()])
    for key, argv in (("interfaces", ["ip", "-json", "address"]),
                      ("routes", ["ip", "-json", "route"]),
                      ("sockets", ["ss", "-antup"]),
                      ("processes", ["ps", "-eo", "pid,ppid,uid,comm"]),
                      ("services", ["systemctl", "list-units", "--type=service", "--no-pager", "--plain"])):
        try:
            output, _, _ = command(argv, timeout=10)
            ctx.finding(section=key, raw=output)
        except Exception as exc:
            ctx.error(f"{key}: {exc}")


def audit(roots, limit, ctx):
    count = 0
    excluded = {"/proc", "/sys", "/dev", "/run"}
    for root in roots:
        root = Path(root).resolve()
        if not root.is_dir():
            ctx.error(f"Diretório inexistente: {root}")
            continue
        for parent, directories, filenames in os.walk(root, followlinks=False, onerror=lambda exc: ctx.error(str(exc))):
            directories[:] = sorted(d for d in directories if str(Path(parent) / d) not in excluded and not (Path(parent) / d).is_symlink())
            for name in sorted(directories + filenames):
                path = Path(parent) / name
                count += 1
                if count > limit:
                    ctx.error(f"Limite de {limit} entradas alcançado")
                    return
                try:
                    info = path.lstat()
                    flags = []
                    if info.st_mode & stat.S_ISUID:
                        flags.append("suid")
                    if info.st_mode & stat.S_ISGID:
                        flags.append("sgid")
                    if info.st_mode & stat.S_IWOTH:
                        flags.append("world_writable")
                    if name.startswith("."):
                        flags.append("hidden")
                    if name in ("id_rsa", "id_ed25519", "credentials", "shadow", ".bash_history", ".mysql_history", ".dockercfg"):
                        flags.append("sensitive_filename")
                    try:
                        pwd.getpwuid(info.st_uid)
                    except KeyError:
                        flags.append("unknown_owner")
                    try:
                        grp.getgrgid(info.st_gid)
                    except KeyError:
                        flags.append("unknown_group")
                    if flags:
                        ctx.finding(path=str(path), mode=stat.filemode(info.st_mode), uid=info.st_uid,
                                    gid=info.st_gid, size=info.st_size, indicators=flags,
                                    confirmed_vulnerability=False)
                except OSError as exc:
                    ctx.error(f"{path}: {exc}")
    ctx.finding(section="scan_summary", entries_inspected=count)


class LinuxInventory(BasePlugin):
    PLUGIN_ID = "linux_inventory"
    ALIASES = ("ops:905",)
    NAME = "Inventário Linux"
    DESCRIPTION = "Inventaria sistema, contas, rede, processos e serviços por seção."
    GROUP = "Red"
    TACTIC = "TA0007"
    ATTACK = (mapping("T1082"),)

    def execute(self, p, ctx):
        inventory(ctx)


class FilesystemAudit(BasePlugin):
    PLUGIN_ID = "filesystem_audit"
    ALIASES = ("ops:906",)
    NAME = "Auditoria de arquivos"
    DESCRIPTION = "Inspeciona nomes, permissões e proprietários sem copiar conteúdo sensível."
    GROUP = "Purple"
    TACTIC = "TA0007"
    ATTACK = (mapping("T1083"),)

    def add_arguments(self, parser):
        parser.add_argument("--roots", nargs="+", type=Path, required=True)
        parser.add_argument("--max-entries", type=positive, default=100000)

    def execute(self, p, ctx):
        audit(p["roots"], p["max_entries"], ctx)


class LocalExposure(FilesystemAudit):
    PLUGIN_ID = "local_exposure_audit"
    ALIASES = ("ops:602",)
    NAME = "Exposição local (JALESC)"
    DESCRIPTION = "Combina inventários e indicadores locais; não executa elevação de privilégios."
    ATTACK = (mapping("T1082"), mapping("T1083"))

    def execute(self, p, ctx):
        inventory(ctx)
        audit(p["roots"], p["max_entries"], ctx)
        for filename in ("/etc/crontab", "/etc/sudoers"):
            path = Path(filename)
            try:
                info = path.stat()
                ctx.finding(section="configuration", path=filename,
                            readable=os.access(path, os.R_OK), mode=stat.filemode(info.st_mode))
            except OSError as exc:
                ctx.error(f"{filename}: {exc}")
        try:
            stdout, _, _ = command(["getcap", "-r", *[str(x.resolve()) for x in p["roots"]]], timeout=30)
            ctx.finding(section="capabilities", raw=stdout)
        except Exception as exc:
            ctx.error(f"Capabilities: {exc}")
