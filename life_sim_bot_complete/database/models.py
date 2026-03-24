import random

def default_player(user_id, background):
    # Get ranges from background or use empty dict if missing
    ranges = background.get("stat_ranges", {})

    return {
        "user_id": user_id,
        "age": 21,
        "jail_until": 0,
        "background": background["name"],
        "money": background["money"],   
        "bank": 0,                       
        "bank_limit": 5000,              
        "debt": 0,                       
        "credit_score": 500,             
        "missed_payments": 0,            
        
        "investments": {                 
            "gold": 0, 
            "crypto": 0
        },
        
        "job": "delivery_worker",
        "job_level": 0,                  
        
        "stats": {
            # Logic: random.randint(min, max) from our JSON
            "intelligence": random.randint(*ranges.get("intelligence", [3, 5])),
            "strength": random.randint(*ranges.get("strength", [3, 5])),
            "charisma": random.randint(*ranges.get("charisma", [3, 5])),
            "dexterity": random.randint(*ranges.get("dexterity", [3, 5])),
            "luck": random.randint(*ranges.get("luck", [3, 5])),
            
            # Fixed ranges or background specific
            "happiness": random.randint(*ranges.get("happiness", [40, 60])),
            "stress": 20,
            "health": 80,
            "energy": 100,
            "reputation": random.randint(*ranges.get("reputation", [0, 10]))
        },
        
        "house": "shelter",              
        "owned_houses": ["shelter"],     
        
        "relationship": None
    }
