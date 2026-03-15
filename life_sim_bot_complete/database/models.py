
def default_player(user_id, background):
    return {
        "user_id": user_id,
        "age": 21,
        "background": background,
        "money": background["money"],
        "job": None,
        "stats": {
            "intelligence": 3,
            "strength": 3,
            "charisma": 3,
            "luck": 3,
            "happiness": 50,
            "stress": 20,
            "health": 80,
            "energy": 100,
            "reputation": 5
        },
        "house": "shelter",
        "relationship": None
    }
