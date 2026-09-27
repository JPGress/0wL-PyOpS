import argparse
import json
import sys
import os
import platform
from pathlib import Path
from dataclasses import asdict
from core.attack import VERSION, TACTICS
from core.operations import execute, EXIT_CODES
from plugins import load_plugins


def metadata(data):
    plugin = data["instance"]
    return {"id": plugin.PLUGIN_ID, "name": plugin.NAME, "description": plugin.DESCRIPTION,
            "group": plugin.GROUP, "kind": plugin.KIND, "status": plugin.STATUS,
            "aliases": plugin.ALIASES, "attack": plugin.ATTACK,
            "dependencies": plugin.DEPENDENCIES, "unavailable": plugin.unavailable(),
            "operations": {name: {"dependencies": dependencies,
                                  "unavailable": plugin.unavailable({plugin.OPERATION_KEY: name})}
                           for name, dependencies in plugin.OPERATION_DEPENDENCIES.items()},
            "automated": plugin.automated}


def main(argv=None):
    registry = load_plugins()
    parser = argparse.ArgumentParser(description="OwL PyOpS — ferramentas e matriz ATT&CK")
    sub = parser.add_subparsers(dest="action")
    listing = sub.add_parser("list")
    for key in ("tactic", "technique", "group", "kind"):
        listing.add_argument("--" + key)
    listing.add_argument("--available", action="store_true")
    listing.add_argument("--format", choices=("text", "json"), default="text")
    info = sub.add_parser("info")
    info.add_argument("plugin")
    run = sub.add_parser("run")
    run.add_argument("plugin")
    run.add_argument("arguments", nargs=argparse.REMAINDER)
    sub.add_parser("doctor")
    matrix = sub.add_parser("matrix")
    matrix.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args(argv)
    for error in registry.errors:
        print(f"Loader: {error}", file=sys.stderr)
    if not args.action:
        from core.menu import render_menu
        from core.dispatcher import Dispatcher
        render_menu()
        Dispatcher.run()
        return 0
    entries = [metadata(data) for data in registry.get_all().values()]
    if args.action in ("info", "run"):
        data = registry.get_plugin(args.plugin)
        if not data:
            parser.error(f"Plugin desconhecido: {args.plugin}")
        plugin = data["instance"]
        if args.action == "info":
            print(json.dumps(metadata(data), ensure_ascii=False, indent=2))
            if plugin.automated:
                plugin.parser().print_help()
            return 0
        if not plugin.automated:
            print("Plugin disponível somente no menu interativo", file=sys.stderr)
            return 3
        plugin_parser = plugin.parser()
        plugin_parser.add_argument("--format", choices=("text", "json"), default="text")
        plugin_parser.add_argument("--output-dir", default="outputs")
        params = vars(plugin_parser.parse_args(args.arguments))
        fmt = params.pop("format")
        output_dir = params.pop("output_dir")
        result = execute(plugin, params, output_dir)
        if fmt == "json":
            print(json.dumps(asdict(result), ensure_ascii=False))
        else:
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        return EXIT_CODES[result.status]
    if args.action == "doctor":
        environment = {"python": platform.python_version(), "platform": platform.system(),
                       "kernel": platform.release(), "uid": os.getuid(),
                       "interfaces": sorted(p.name for p in Path("/sys/class/net").glob("*")),
                       "wireless_interfaces": sorted(p.parent.name for p in Path("/sys/class/net").glob("*/phy80211")),
                       "note": "Presença de dependência/interface não comprova permissões nem validação operacional."}
        print(json.dumps({"environment": environment, "loader_errors": registry.errors, "plugins": entries}, ensure_ascii=False, indent=2))
        return 1 if registry.errors else 0
    if args.action == "list":
        for key in ("group", "kind"):
            if getattr(args, key):
                entries = [entry for entry in entries if entry[key] == getattr(args, key)]
        for key in ("tactic", "technique"):
            if getattr(args, key):
                entries = [e for e in entries if any(m[key] == getattr(args, key) for m in e["attack"])]
        if args.available:
            entries = [e for e in entries if not e["unavailable"]]
        if args.format == "json":
            print(json.dumps(entries, ensure_ascii=False, indent=2))
        else:
            for entry in entries:
                print(f"{entry['id']}: {entry['name']} [{entry['status']}; {entry['kind']}]"
                      + (" — " + "; ".join(entry["unavailable"]) if entry["unavailable"] else ""))
        return 0
    rows = []
    for tactic, name in TACTICS.items():
        found = False
        for entry in entries:
            for relation in entry["attack"]:
                if relation["tactic"] != tactic:
                    continue
                found = True
                rows.append({"tactic": tactic, "name": name, "technique": relation["technique"],
                             "plugin": entry["id"], "kind": entry["kind"],
                             "state": "unavailable" if entry["unavailable"] else entry["status"],
                             "context": relation.get("context", ""),
                             "validated": entry["kind"] == "tool" and entry["status"] == "ready" and not entry["unavailable"]})
        if not found:
            rows.append(dict(tactic=tactic, name=name, technique="—", plugin="—", kind="—",
                             state="gap", context="", validated=False))
    if args.format == "json":
        print(json.dumps({"attack_version": VERSION, "rows": rows}, ensure_ascii=False, indent=2))
    else:
        print(f"# ATT&CK Enterprise {VERSION}\n\n| Tática | Técnica | Plugin | Tipo | Estado | Contexto |\n|---|---|---|---|---|---|")
        for row in rows:
            print("| " + " | ".join(str(row[k]) for k in ("tactic", "technique", "plugin", "kind", "state", "context")) + " |")
    return 0
