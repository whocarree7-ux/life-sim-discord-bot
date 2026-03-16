import discord
from discord.ext import commands
from discord import app_commands
import random
import time
from database.db import players
from systems.minigame_manager import MinigameManager

class Crime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mg_manager = MinigameManager()
        self.crime_cooldowns = {}

    @app_commands.command(name="crime", description="Commit a small crime for quick cash")
    async def crime(self, interaction: discord.Interaction):
        player = await players.find_one({"user_id": interaction.user.id})
        if not player: return await interaction.response.send_message("❌ Start your life first!", ephemeral=True)

        # Logic: High risk, medium reward
        success = await self.mg_manager.run(interaction, "random") # Trigger a minigame

        if success:
            loot = random.randint(200, 800)
            await players.update_one({"user_id": interaction.user.id}, {"$inc": {"money": loot, "stats.reputation": -10}})
            await interaction.followup.send(f"💸 You robbed a convenience store and got **${loot}**! (Reputation decreased)")
        else:
            penalty = 200
            await players.update_one({"user_id": interaction.user.id}, {"$inc": {"money": -penalty, "stats.reputation": -5}})
            await interaction.followup.send(f"👮 You got caught! You paid a **${penalty}** fine.")

    @app_commands.command(name="steal", description="Attempt to steal money from another player")
    @app_commands.describe(target="The player you want to rob")
    async def steal(self, interaction: discord.Interaction, target: discord.Member):
        if target.id == interaction.user.id:
            return await interaction.response.send_message("❌ You can't steal from yourself!", ephemeral=True)

        # Check if target exists
        victim = await players.find_one({"user_id": target.id})
        if not victim or victim.get("money", 0) < 100:
            return await interaction.response.send_message(f"❌ {target.name} is too poor to rob!", ephemeral=True)

        # Success Chance (e.g., 40%)
        if random.random() < 0.40:
            stolen = int(victim["money"] * random.uniform(0.1, 0.3)) # Steal 10-30%
            await players.update_one({"user_id": interaction.user.id}, {"$inc": {"money": stolen}})
            await players.update_one({"user_id": target.id}, {"$inc": {"money": -stolen}})
            await interaction.response.send_message(f"🧤 Success! You stole **${stolen}** from {target.mention}!")
        else:
            await interaction.response.send_message(f"🚨 You failed to rob {target.mention} and ran away!")

async def setup(bot):
    await bot.add_cog(Crime(bot))
          
