from __future__ import annotations

DEFAULT_CATEGORIES = [
    "Survival",
    "Build",
    "Family",
    "Home",
    "Body",
    "Admin",
    "Joy",
    "Recovery",
    "Social",
    "Errands",
]

ALIASES = {
    "health": "Body",
    "self care": "Body",
    "self-care": "Body",
    "chores": "Home",
    "clean": "Home",
    "laundry": "Home",
    "bills": "Admin",
    "paperwork": "Admin",
    "admin": "Admin",
    "client": "Build",
    "code": "Build",
    "coding": "Build",
    "work": "Build",
    "nspl": "Build",
    "rohtalk": "Build",
    "liferpg": "Build",
    "dad": "Family",
    "family": "Family",
    "water": "Body",
    "brush": "Body",
    "walk": "Body",
    "move": "Body",
    "groceries": "Errands",
    "call": "Social",
    "rest": "Recovery",
    "sleep": "Recovery",
    "game": "Joy",
}


def canonical_category(value: str | None, *, text: str = "") -> str:
    if value:
        cleaned = str(value).strip()
        for category in DEFAULT_CATEGORIES:
            if cleaned.casefold() == category.casefold():
                return category
        alias = ALIASES.get(cleaned.casefold())
        if alias:
            return alias

    haystack = f"{value or ''} {text}".casefold()
    for needle, category in ALIASES.items():
        if needle in haystack:
            return category
    return "Survival"
