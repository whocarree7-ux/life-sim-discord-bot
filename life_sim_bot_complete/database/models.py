def default_player(user_id, background):
    return {
        "user_id": user_id,
        "age": 21,
        "background": background,
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
        
        # --- JOB & PROMOTION UPDATE ---
        "job": "delivery_worker",
        "job_level": 0,                  # 0 = Entry, 1-3 = Promoted
        
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
        "owned_houses": ["shelter"],     
        
        "relationship": None
    }
