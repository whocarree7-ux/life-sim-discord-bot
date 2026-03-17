def default_player(user_id, background):
    return {
        "user_id": user_id,
        "age": 21,
        "background": background["name"], # Just save the name string
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
            "intelligence": 3,
            "strength": 3,
            "charisma": 3,
            "dexterity": 3,      # <--- ADDED THIS
            "luck": 3,
            "happiness": 50,
            "stress": 20,
            "health": 80,
            "energy": 100,
            "reputation": 5,
            "wanted_level": 0    # <--- USEFUL FOR CRIME
        },
        
        "is_jailed": False,      # <--- USEFUL FOR CRIME
        "house": "shelter",              
        "owned_houses": ["shelter"],     
        
        "relationship": None
    }
