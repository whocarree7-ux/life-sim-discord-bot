import random

# Calculate if a steal is successful based on stats
def calculate_steal_chance(thief_stats, victim_stats):
    base_chance = 0.40
    # Thief's dexterity helps, Victim's strength makes it harder
    dex_bonus = thief_stats.get('dexterity', 0) * 0.01
    str_penalty = victim_stats.get('strength', 0) * 0.005
    
    chance = base_chance + dex_bonus - str_penalty
    return max(0.1, min(0.9, chance)) # Keep chance between 10% and 90%

def get_random_crime():
    crimes = [
        {
            "name": "Pickpocket",
            "desc": "You tried to swipe a wallet from a busy commuter.",
            "min_loot": 50, "max_loot": 200, "penalty": 100, "rep_loss": -2
        },
        {
            "name": "ATM Hack",
            "desc": "You installed a skimmer on a local ATM.",
            "min_loot": 500, "max_loot": 1200, "penalty": 400, "rep_loss": -10
        },
        {
            "name": "Shop Lifting",
            "desc": "You tried to walk out of Arcadia Mall with a designer watch.",
            "min_loot": 300, "max_loot": 700, "penalty": 250, "rep_loss": -5
        },
        {
            "name": "Graffiti Art",
            "desc": "You spray-painted the side of the Police Station.",
            "min_loot": 10, "max_loot": 50, "penalty": 500, "rep_loss": -15
        }
    ]
    return random.choice(crimes)
