# Use this to calculate if a crime is successful based on player stats
def calculate_steal_chance(thief_stats, victim_stats):
    base_chance = 0.40
    # Thief's speed/dexterity could increase chance
    # Victim's strength could decrease it
    return base_chance + (thief_stats.get('dexterity', 0) * 0.01)
