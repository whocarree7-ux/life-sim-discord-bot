import discord
from discord.ext import commands
from discord import app_commands
import random
import time
from database.db import players
from systems.minigame_manager import MinigameManager
from systems.crime_system import calculate_steal_chance, get_random_crime

class Crime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mg_manager = MinigameManager()
        self.cooldowns = {}

    @app_commands.command(name="crime", description="Commit a random crime in Arcadia")
    async def crime(self, interaction: discord.Interaction):
        player = await players.find_one({"user_id": interaction.user.id})
        if not player: return await interaction.response.send_message("❌ Start your life first!", ephemeral=True)

        scenario = get_random_crime()
        success = await self.mg_manager.run(interaction, "random")

        if success:
            loot = random.randint(scenario['min_loot'], scenario['max_loot'])
            await players.update_one(
                {"user_id": interaction.user.id}, 
                {"$inc": {"money": loot, "stats.reputation": scenario['rep_loss']}}
            )
            await interaction.followup.send(f"✅ **{scenario['name']}**: {scenario['desc']}\nYou walked away with **${loot}**!")
        else:
            await players.update_one(
                {"user_id": interaction.user.id}, 
                {"$inc": {"money": -scenario['penalty'], "stats.reputation": scenario['rep_loss']}}
            )
            await interaction.followup.send(f"👮 **Failed**: You were caught! You paid a **${scenario['penalty']}** fine.")

    @app_commands.command(name="steal", description="Steal cash directly from another player's wallet")
    @app_commands.describe(target="The player you want to rob")
    async def steal(self, interaction: discord.Interaction, target: discord.Member):
        if target.id == interaction.user.id:
            return await interaction.response.send_message("❌ You can't rob yourself.", ephemeral=True)

        thief = await players.find_one({"user_id": interaction.user.id})
        victim = await players.find_one({"user_id": target.id})

        if not thief or not victim:
            return await interaction.response.send_message("❌ One of you hasn't started their life yet!", ephemeral=True)
        if victim.get("money", 0) < 100:
            return await interaction.response.send_message("❌ Target is too poor to rob.", ephemeral=True)

        chance = calculate_steal_chance(thief.get('stats', {}), victim.get('stats', {}))
        
        if random.random() < chance:
            stolen = int(victim["money"] * random.uniform(0.1, 0.25))
            await players.update_one({"user_id": interaction.user.id}, {"$inc": {"money": stolen}})
            await players.update_one({"user_id": target.id}, {"$inc": {"money": -stolen}})
            await interaction.response.send_message(f"🧤 **Success!** You snuck into {target.mention}'s pockets and took **${stolen}**.")
        else:
            fail_fine = 150
            await players.update_one({"user_id": interaction.user.id}, {"$inc": {"money": -fail_fine}})
            await interaction.response.send_message(f"🚨 **Busted!** {target.mention} caught you! You dropped **${fail_fine}** while running.")

    @app_commands.command(name="heist", description="High-stakes bank robbery. Massive reward, massive risk.")
    async def heist(self, interaction: discord.Interaction):
        # Heists require a minigame and have a 1-hour cooldown
        success = await self.mg_manager.run(interaction, "puzzle") # Force a puzzle for heists

        if success:
            loot = random.randint(5000, 15000)
            await players.update_one({"user_id": interaction.user.id}, {"$inc": {"bank": loot, "stats.reputation": -50}})
            await interaction.followup.send(f"🏦 **HEIST SUCCESS!** You cracked the vault and cleaned out **${loot}**!")
        else:
            await players.update_one({"user_id": interaction.user.id}, {"$set": {"money": 0}, "$inc": {"stats.reputation": -30}})
            await interaction.followup.send("🚑 **HEIST FAILED**: The SWAT team arrived. You lost all your pocket cash!")

    @app_commands.command(name="hack", description="Hack into the Arcadia mainframe for digital credits")
    async def hack(self, interaction: discord.Interaction):
        # Hack relies on Intelligence stat
        player = await players.find_one({"user_id": interaction.user.id})
        intel = player.get('stats', {}).get('intelligence', 0)
        
        success = await self.mg_manager.run(interaction, "typing") # Force a typing game

        if success:
            reward = 1000 + (intel * 10)
            await players.update_one({"user_id": interaction.user.id}, {"$inc": {"money": reward}})
            await interaction.followup.send(f"💻 **HACKED**: You bypassed the firewall and redirected **${reward}** to your account.")
        else:
            await interaction.followup.send("📡 **ERROR**: Your IP was traced. You had to abandon the hardware!")

async def setup(bot):
    await bot.add_cog(Crime(bot))
