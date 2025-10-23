# app/game_rules.py


DERIVED_SKILLS = {
    "moha": ("prajna", "samkalpa"),      # Charm / Deception
    "bhaya": ("bala", "samkalpa"),       # Intimidation
    "chhalana": ("dakshata", "buddhi"),  # Stealth / Sleight of Hand
    "anveshana": ("buddhi", "prajna"),   # Investigation
    "sahanashakti": ("dhriti", "samkalpa"), # Resilience / Fortitude (resisting effects)
    "yukti": ("dakshata", "prajna"),          # Tactics / Strategy (battlefield assessment)
    "prerana": ("prajna", "samkalpa"),      # Performance / Inspiration (influencing crowds)
    "atindriya": ("bala", "prajna"),      # Perception / Insight (noticing details)
}

ATTRIBUTE_TO_RESOURCE = {
    "bala": "tapas", "dakshata": "tapas", "dhriti": "tapas",
    "buddhi": "maya", "prajna": "maya", "samkalpa": "maya",
}


DEFAULT_EQUIPMENT_BY_CLASS = {
    "Yodha": [
        ("Gada", 1),
        ("Loha Kavacha", 1),  
        ("Sanjeevani Ras", 2),
    ],
    "Rishi": [
        ("Mantradanda", 1),   
        ("Shankha", 1),
        ("Sanjeevani Ras", 1),
    ],
    "Dhanurdhara": [
        ("Dhanush", 1),
        ("Charma", 1),
        ("Rope (50ft)", 1),
    ],
    "Chara": [
        ("Khadga", 1),
        ("Charma", 1),
        ("Torch", 5),
    ],
    "Sutradhara": [
        ("Khadga", 1),
        ("Flute", 1),
        ("Parchment", 5),
    ],
}