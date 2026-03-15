import discord
from discord.ext import commands, tasks # Added tasks
from database.db import players

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.add_interest.start() # Start the interest loop

    def cog_unload(self):
        self.add_interest.cancel() # Stop loop if cog is reloaded

    @tasks.loop(hours=24) # Runs once every 24 hours
    async def add_interest(self):
        """Adds 1% interest to everyone's bank balance daily."""
        interest_rate = 0.01 
        
        # This MongoDB command updates ALL players who have money in the bank
        await players.update_many(
            {"bank": {"$gt": 0}}, 
            [{"$set": {"bank": {"$add": ["$bank", {"$multiply": ["$bank", interest_rate]}]}}}]
        )
        print("💰 Daily interest distributed.")

    @commands.command(aliases=["dep"])
    async def deposit(self, ctx, amount: str):
        # ... (Your existing deposit code)
        pass

    @commands.command(aliases=["with"])
    async def withdraw(self, ctx, amount: str):
        # ... (Your existing withdraw code)
        pass

async def setup(bot):
    await bot.add_cog(Economy(bot))
    
