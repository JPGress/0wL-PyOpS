"""Registro determinístico com aliases e compatibilidade com o menu original."""
class PluginRegistry:
    def __init__(self):
        self.clear()

    def clear(self):
        self.plugins = {}
        self.aliases = {}
        self.groups = {name: {} for name in ("Red", "Blue", "Purple", "Misc")}
        self.errors = []

    def register(self, plugin_id, name, group, tactic, description, callback, instance=None):
        aliases = tuple(instance.ALIASES) if instance else ()
        keys = (plugin_id,) + aliases
        if not all(isinstance(k, str) and k and not any(c.isspace() for c in k) for k in keys):
            raise ValueError("IDs/aliases devem ser strings não vazias sem espaços")
        if len(keys) != len(set(keys)) or any(k in self.plugins or k in self.aliases for k in keys):
            raise ValueError(f"Colisão de ID/alias: {plugin_id}")
        if group not in self.groups or not name or not description:
            raise ValueError(f"Metadados inválidos: {plugin_id}")
        if instance:
            from core.attack import validate
            validate(instance)
        data = dict(id=plugin_id, name=name, group=group, tactic=tactic,
                    description=description, callback=callback, instance=instance)
        self.plugins[plugin_id] = data
        self.aliases.update({key: plugin_id for key in aliases})
        tactics = sorted({m["tactic"] for m in instance.ATTACK}) if instance and instance.ATTACK else [tactic]
        for key in tactics:
            self.groups[group].setdefault(key, []).append(data)

    def get_plugin(self, plugin_id):
        return self.plugins.get(self.aliases.get(plugin_id, plugin_id))

    def get_all(self):
        return self.plugins

    def get_groups(self):
        return self.groups

registry = PluginRegistry()
