from __future__ import annotations

DEFAULT_PROJECT = "General"

DEFAULT_PROJECTS = [
    DEFAULT_PROJECT,
    "NSPL",
    "LifeRPG",
    "RohTalk",
    "Household",
    "Family",
    "Personal",
    "Client Work",
]

ALIASES = {
    "nspl": "NSPL",
    "nodectx": "NSPL",
    "entry": "NSPL",
    "liferpg": "LifeRPG",
    "life rpg": "LifeRPG",
    "quest": "LifeRPG",
    "rohtalk": "RohTalk",
    "roh talk": "RohTalk",
    "roh": "RohTalk",
    "house": "Household",
    "home": "Household",
    "laundry": "Household",
    "dishes": "Household",
    "family": "Family",
    "parent": "Family",
    "health": "Personal",
    "water": "Personal",
    "walk": "Personal",
    "rest": "Personal",
    "client": "Client Work",
    "invoice": "Client Work",
}


def canonical_project(value: str | None, *, text: str = "") -> str:
    if value:
        cleaned = str(value).strip()
        if cleaned:
            for project in DEFAULT_PROJECTS:
                if cleaned.casefold() == project.casefold():
                    return project
            alias = ALIASES.get(cleaned.casefold())
            if alias:
                return alias
            return cleaned

    haystack = f"{value or ''} {text}".casefold()
    for needle, project in ALIASES.items():
        if needle in haystack:
            return project
    return DEFAULT_PROJECT
