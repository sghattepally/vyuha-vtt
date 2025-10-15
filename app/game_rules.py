# app/game_rules.py

# This file acts as our digital Player's Handbook for the backend.

CLASS_TEMPLATES = {
    "Yodha": {
        "attributes": {"bala": 15, "dakshata": 13, "dhriti": 14, "buddhi": 8, "prajna": 10, "samkalpa": 12},
        "max_tapas": 4,
        "max_maya": 0
    },
    "Rishi": {
        "attributes": {"bala": 8, "dakshata": 12, "dhriti": 13, "buddhi": 14, "prajna": 15, "samkalpa": 10},
        "max_tapas": 0,
        "max_maya": 4
    },
    "Dhanurdhara": {
        "attributes": {"bala": 10, "dakshata": 15, "dhriti": 13, "buddhi": 14, "prajna": 12, "samkalpa": 8},
        "max_tapas": 2, # Example: Hybrid classes start with a split pool
        "max_maya": 2
    },
    "Chara": {
        "attributes": {"bala": 10, "dakshata": 14, "dhriti": 8, "buddhi": 15, "prajna": 13, "samkalpa": 12},
        "max_tapas": 2,
        "max_maya": 2
    },
    "Sutradhara": {
        "attributes": {"bala": 8, "dakshata": 13, "dhriti": 12, "buddhi": 10, "prajna": 15, "samkalpa": 14},
        "max_tapas": 0,
        "max_maya": 4
    }
}

def get_attribute_modifier(score: int) -> int:
    """Calculates the modifier for a given attribute score."""
    return (score - 10) // 2