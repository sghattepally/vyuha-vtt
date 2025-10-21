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

