def default_player(user_id, background):
    return {
        "user_id": user_id,
        "age": 21,
        "background": background,
        "money": background["money"],   # Cash in wallet
        "bank": 0,                       # Bank balance
        "bank_limit": 5000,              # Max bank capacity
        "debt": 0,                       # Total amount owed to the bank
        "credit_score": 500,             # Affects loan limits (Standard is 500)
        "missed_payments": 0,            # Tracks days for the 3-day seizure rule
        
        "investments": {                 # Investment Portfolio
            "gold": 0, 
            "crypto": 0
        },
        
        "job": "delivery_worker",
        
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
        
        # --- HOUSING UPDATE ---
        "house": "shelter",              # Current active residence
        "owned_houses": ["shelter"],     # List of all properties the player owns
        
        "relationship": None
    }
