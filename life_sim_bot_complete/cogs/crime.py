import discord
from discord.ext import commands
from discord import app_commands
import random
from database.db import players
from systems.minigame_manager import MinigameManager
from systems.crime_system import calculate_steal_chance, get_random_crime

class Crime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mg_manager = MinigameManager()

    @app_commands.command(name="crime", description="Commit a random crime (Typing Test - 15⚡)")
    async def crime(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            player = await players.find_one({"user_id": interaction.user.id})
            if not player: 
                return await interaction.followup.send("❌ Start your life first!")
            
            energy = player.get("stats", {}).get("energy", 0)
            if energy < 15:
                return await interaction.followup.send(f"❌ You are too tired! (Need 15⚡, have {energy}⚡)")

            # --- GAME LOGIC: TYPING (5 SECONDS) ---
            success = await self.mg_manager.run(interaction, "typing") 
            scenario = get_random_crime()

            if success:
                loot = random.randint(scenario['min_loot'], scenario['max_loot'])
                await players.update_one(
                    {"user_id": interaction.user.id}, 
                    {"$inc": {"money": loot, "stats.reputation": scenario['rep_loss'], "stats.energy": -15}}
                )
                await interaction.followup.send(f"✅ **{scenario['name']}**: {scenario['desc']}\nYou walked away with **${loot}**! (-15⚡)")
            else:
                await players.update_one(
                    {"user_id": interaction.user.id}, 
                    {"$inc": {"money": -scenario['penalty'], "stats.reputation": scenario['rep_loss'], "stats.energy": -5}}
                )
                # The 'Failed' message is often handled inside the typing game, but we add a summary here
                await interaction.followup.send(f"👮 **Busted**: You paid a **${scenario['penalty']}** fine and lost 5⚡.")

        except Exception as e:
            print(f"Crime Error Logic: {e}")
            await interaction.followup.send("⚠️ The system encountered an error while starting the crime.")

    @app_commands.command(name="heist", description="High-stakes bank robbery (Emoji Game - 40⚡)")
    async def heist(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            player = await players.find_one({"user_id": interaction.user.id})
            energy = player.get("stats", {}).get("energy", 0) if player else 0
            
            if energy < 40:
                return await interaction.followup.send(f"❌ Heists require 40⚡! You only have {energy}⚡.")

            # --- GAME LOGIC: MEMORY (EMOJI GAME) ---
            success = await self.mg_manager.run(interaction, "memory") 

            if success:
                loot = random.randint(5000, 15000)
                await players.update_one(
                    {"user_id": interaction.user.id}, 
                    {"$inc": {"bank": loot, "stats.reputation": -50, "stats.energy": -40}}
                )
                await interaction.followup.send(f"🏦 **HEIST SUCCESS!** You cracked the vault and cleaned out **${loot}**! (-40⚡)")
            else:
                await players.update_one(
                    {"user_id": interaction.user.id}, 
                    {"$set": {"money": 0}, "$inc": {"stats.reputation": -30, "stats.energy": -10}}
                )
                await interaction.followup.send("🚑 **HEIST FAILED**: SWAT arrived! You lost all pocket cash and 10⚡.")
        except Exception as e:
            print(f"Heist Error Logic: {e}")
            await interaction.followup.send("⚠️ The heist system glitched.")

    @app_commands.command(name="hack", description="Hack the mainframe (Reaction Test - 20⚡)")
    async def hack(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            player = await players.find_one({"user_id": interaction.user.id})
            if not player: 
                return await interaction.followup.send("❌ Start your life first!")
            
            energy = player.get("stats", {}).get("energy", 0)
            if energy < 20:
                return await interaction.followup.send(f"❌ Need 20⚡ to hack!")

            # --- GAME LOGIC: REACTION ---
            success = await self.mg_manager.run(interaction, "reaction") 

            if success:
                intel = player.get('stats', {}).get('intelligence', 0)
                reward = 1000 + (intel * 10)
                await players.update_one(
                    {"user_id": interaction.user.id}, 
                    {"$inc": {"money": reward, "stats.energy": -20}}
                )
                await interaction.followup.send(f"💻 **HACKED**: You bypassed the firewall and redirected **${reward}**. (-20⚡)")
            else:
                await players.update_one({"user_id": interaction.user.id}, {"$inc": {"stats.energy": -5}})
                # Failure message is usually sent by the reaction game
        except Exception as e:
            print(f"Hack Error Logic: {e}")
            await interaction.followup.send("⚠️ Connection to mainframe lost.")

    @app_commands.command(name="steal", description="Rob a player (Costs 10⚡)")
    @app_commands.describe(target="The player you want to rob")
    async def steal(self, interaction: discord.Interaction, target: discord.Member):
        if target.id == interaction.user.id:
            return await interaction.response.send_message("❌ You can't rob yourself.", ephemeral=True)

        thief = await players.find_one({"user_id": interaction.user.id})
        victim = await players.find_one({"user_id": target.id})

        if not thief or not victim:
            return await interaction.response.send_message("❌ One of you hasn't started their life yet!", ephemeral=True)
        
        energy = thief.get("stats", {}).get("energy", 0)
        if energy < 10:
            return await interaction.response.send_message(f"❌ Need 10⚡ to steal!", ephemeral=True)

        if victim.get("money", 0) < 100:
            return await interaction.response.send_message("❌ Target is too poor to rob.", ephemeral=True)

        chance = calculate_steal_chance(thief.get('stats', {}), victim.get('stats', {}))
        
        if random.random() < chance:
            stolen = int(victim["money"] * random.uniform(0.1, 0.25))
            await players.update_one({"user_id": interaction.user.id}, {"$inc": {"money": stolen, "stats.energy": -10}})
            await players.update_one({"user_id": target.id}, {"$inc": {"money": -stolen}})
            await interaction.response.send_message(f"🧤 **Success!** You took **${stolen}** from {target.mention}. (-10⚡)")
        else:
            await players.update_one({"user_id": interaction.user.id}, {"$inc": {"money": -150, "stats.energy": -5}})
            await interaction.response.send_message(f"🚨 **Busted!** You dropped **$150** while running away.")

async def setup(bot):
    await bot.add_cog(Crime(bot))