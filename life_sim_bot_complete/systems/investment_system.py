import random

class InvestmentSystem:
    def __init__(self):
        # Starting prices
        self.prices = {
            "gold": 1500,
            "crypto": 35000
        }

    def update_market(self):
        """Randomly fluctuate prices."""
        # Gold is stable (changes 1-3%)
        gold_change = random.uniform(-0.03, 0.03)
        # Crypto is volatile (changes 5-15%)
        crypto_change = random.uniform(-0.15, 0.15)

        self.prices["gold"] = max(100, int(self.prices["gold"] * (1 + gold_change)))
        self.prices["crypto"] = max(1000, int(self.prices["crypto"] * (1 + crypto_change)))
        
        return self.prices

# Global instance to be used by the Cog
market = InvestmentSystem()
