# app/game_rules.py


# ===============================================================
# UPDATED: Class Data
# Renaming 'attributes' to 'base_attributes' to match our database model.
# ===============================================================
CLASSES = {
    "Yodha": {
        "description": "A master of combat who channels their inner fire (Tapas) to achieve unmatched physical prowess. The quintessential warrior.",
        "primary_attribute": "Bala",
        "base_attributes": {"bala": 15, "dakshata": 13, "dhriti": 14, "buddhi": 8, "prajna": 10, "samkalpa": 12}
    },
    "Rishi": {
        "description": "A sage who has mastered the art of Māyā, projecting their spirit to influence reality and command potent spiritual power.",
        "primary_attribute": "Prajna",
        "base_attributes": {"bala": 8, "dakshata": 12, "dhriti": 13, "buddhi": 14, "prajna": 15, "samkalpa": 10}
    },
    "Dhanurdhara": {
        "description": "A peerless archer who blends physical discipline with heightened awareness, striking their foes from afar with deadly precision.",
        "primary_attribute": "Dakshata",
        "base_attributes": {"bala": 10, "dakshata": 15, "dhriti": 13, "buddhi": 14, "prajna": 12, "samkalpa": 8}
    },
    "Chara": {
        "description": "A cunning scout and trickster who uses their intellect and agility to navigate dangers and outwit their enemies.",
        "primary_attribute": "Buddhi",
        "base_attributes": {"bala": 10, "dakshata": 14, "dhriti": 8, "buddhi": 15, "prajna": 13, "samkalpa": 12}
    },
    "Sutradhara": {
        "description": "A charismatic leader and manipulator whose strength lies in their force of will, influencing the hearts and minds of others.",
        "primary_attribute": "Samkalpa",
        "base_attributes": {"bala": 8, "dakshata": 13, "dhriti": 12, "buddhi": 10, "prajna": 15, "samkalpa": 14}
    }
}

# (The get_attribute_modifier function can be removed from here later, 
# as this logic will live in the backend API when we calculate stats)
def get_attribute_modifier(score: int) -> int:
    """Calculates the modifier for a given attribute score."""
    return (score - 10) // 2