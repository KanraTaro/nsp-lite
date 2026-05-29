from __future__ import annotations


CATEGORIES = (
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
)

HABIT_CADENCE = ("daily", "weekdays", "weekly", "monthly", "custom")
QUEST_STATUS = ("open", "active", "paused", "completed", "archived")
EVENT_STATUS = ("scheduled", "active", "complete", "archived")
REWARD_INTENSITY = ("low", "normal", "high")
STRICTNESS_MODE = ("gentle", "balanced", "hard", "custom")
VISUAL_MODE = ("command_center", "compact", "mobile")
RATING_1_TO_5 = tuple(str(value) for value in range(1, 6))


def all_choices() -> dict[str, tuple[str, ...]]:
    return {
        "categories": CATEGORIES,
        "habit_cadence": HABIT_CADENCE,
        "quest_status": QUEST_STATUS,
        "event_status": EVENT_STATUS,
        "reward_intensity": REWARD_INTENSITY,
        "strictness_mode": STRICTNESS_MODE,
        "visual_mode": VISUAL_MODE,
        "ratings": RATING_1_TO_5,
    }
