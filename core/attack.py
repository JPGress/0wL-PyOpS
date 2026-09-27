"""Recorte revisado do ATT&CK Enterprise v19.2, sem atualização em runtime.
Fontes: https://attack.mitre.org/resources/versions/ e páginas das técnicas.
"""
VERSION = "19.2"
TECHNIQUES = {
    "T1589": ("TA0043",), "T1592.002": ("TA0043",),
    "T1590.002": ("TA0043",), "T1596.002": ("TA0043",),
    "T1596.003": ("TA0043",), "T1593.002": ("TA0043",),
    "T1594": ("TA0043",), "T1595": ("TA0043",),
    "T1595.002": ("TA0043",), "T1046": ("TA0007",),
    "T1135": ("TA0007",), "T1082": ("TA0007",),
    "T1083": ("TA0007",), "T1018": ("TA0007",),
    "T1557.002": ("TA0006", "TA0009"),
    "T1040": ("TA0006", "TA0007"), "T1110.002": ("TA0006",),
}
TACTICS = {"TA0043": "Reconnaissance", "TA0042": "Resource Development",
           "TA0001": "Initial Access", "TA0002": "Execution", "TA0003": "Persistence",
           "TA0004": "Privilege Escalation", "TA0005": "Stealth", "TA0112": "Defense Impairment",
           "TA0006": "Credential Access",
           "TA0007": "Discovery", "TA0008": "Lateral Movement", "TA0009": "Collection",
           "TA0011": "Command and Control", "TA0010": "Exfiltration", "TA0040": "Impact"}


def mapping(technique, context=None):
    value = {"tactic": TECHNIQUES[technique][0], "technique": technique,
             "source": "https://attack.mitre.org/techniques/" + technique.replace(".", "/") + "/",
             "rationale": "Comportamento documentado no catálogo de portabilidade"}
    if context:
        value["context"] = context
    return value


def validate(plugin):
    if plugin.KIND not in ("tool", "reference") or plugin.STATUS not in ("ready", "experimental"):
        raise ValueError("KIND/STATUS inválido")
    for item in plugin.ATTACK:
        if item.get("tactic") not in TECHNIQUES.get(item.get("technique"), ()):
            raise ValueError(f"Relação ATT&CK inválida: {item}")
