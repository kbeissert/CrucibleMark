from utils.module_registry import get_active_modules
import yaml
with open("benchmark_config.yaml", "r") as f:
    cfg = yaml.safe_load(f)
mods = get_active_modules(cfg)
for m_id, meta, inner in mods:
    merged = meta.copy()
    merged.update(inner.get("metadata", {}))
    print(f"Modul: {m_id}, ID in merged: {merged.get('id')}")
