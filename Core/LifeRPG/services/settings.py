from __future__ import annotations

from Core.LifeRPG.defaults import DEFAULT_SETTINGS, ensure_defaults


def get_settings(store) -> dict:
    ensure_defaults(store)
    settings = store.read_json("Config", "", "settings.json")
    profile = store.read_json("Config", "", "profile.json")
    result = dict(DEFAULT_SETTINGS)
    if isinstance(settings, dict):
        result.update(settings)
    if isinstance(profile, dict):
        result.update({k: v for k, v in profile.items() if k in {"display_name", "timezone", "default_scope"}})
    return result


def update_settings(store, **updates) -> dict:
    current = get_settings(store)
    for key, value in updates.items():
        if value is None:
            continue
        if key == "auto_sort_enabled":
            current[key] = str(value).strip().casefold() in {"1", "true", "yes", "on"}
        elif key == "checkin_minutes":
            current[key] = max(5, int(value or current.get(key, 90)))
        elif key in current:
            current[key] = str(value).strip() if isinstance(value, str) else value
    store.write_json("Config", "", "settings.json", current)
    store.write_json(
        "Config",
        "",
        "profile.json",
        {k: current[k] for k in ["display_name", "timezone", "default_scope"] if k in current},
    )
    store.append_event("settings_updated", {"keys": sorted(updates.keys())})
    return current
