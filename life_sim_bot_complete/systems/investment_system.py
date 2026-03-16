import random


class InvestmentSystem:

    def __init__(self):

        # starting prices
        self.markets = {
            "gold": 1500,
            "crypto": 35000
        }

    def update_market(self):

        # gold changes slowly
        gold_change = random.uniform(-0.03, 0.08)

        # crypto is volatile
        crypto_change = random.uniform(-0.15, 0.80)

        self.markets["gold"] = max(
            100,
            int(self.markets["gold"] * (1 + gold_change))
        )

        self.markets["crypto"] = max(
            1000,
            int(self.markets["crypto"] * (1 + crypto_change))
        )

        return self.markets


# global instance
market = InvestmentSystem()