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

    async def get_working_context(self, ctx):
        if ctx.interaction:
            if not ctx.interaction.response.is_done():
                await ctx.interaction.response.defer()
            ctx.send = ctx.interaction.followup.send
        return ctx

    @commands.hybrid_command(name="crime", description="Commit a random crime (15⚡)")
    async def crime(self, ctx):
        ctx = await self.get_working_context(ctx)
        player = await players.find_one({"user_id": ctx.author.id})
        if not player: return await ctx.send("❌ Start your life first!")
        
        # Developer Suggestion: Wanted Level scaling
        # High wanted level makes minigames harder or reduces loot
        wanted = player.get("stats", {}).get("reputation", 0)
        
        energy = player.get("stats", {}).get("energy", 0)
        if energy < 15: return await ctx.send(f"❌ Too tired! ({energy}/15⚡)")

        success = await self.mg_manager.run(ctx, "typing") 
        scenario = get_random_crime()

        if success:
            # Chance System: Even if minigame is won, there's a 10% 'bad luck' factor
            if random.random() < 0.10:
                return await ctx.send("🕵️ The police were watching! You had to ditch the loot and run.")

            loot = random.randint(scenario['min_loot'], scenario['max_loot'])
            await players.update_one(
                {"user_id": ctx.author.id}, 
                {"$inc": {"money": loot, "stats.reputation": scenario['rep_loss'], "stats.energy": -15}}
            )
            await ctx.send(f"✅ **{scenario['name']}**: {scenario['desc']}\nEarned **${loot}**! (-15⚡)")
        else:
            # Penalty increases if you are already a known criminal
            penalty = scenario['penalty']
            if wanted < -100: penalty = int(penalty * 1.5)
            
            await players.update_one(
                {"user_id": ctx.author.id}, 
                {"$inc": {"money": -penalty, "stats.reputation": scenario['rep_loss'], "stats.energy": -5}}
            )
            await ctx.send(f"👮 **Busted**: You paid a **${penalty}** fine. (Repeat offenders pay more!)")

    @commands.hybrid_command(name="heist", description="High-stakes bank robbery (40⚡)")
    async def heist(self, ctx):
        ctx = await self.get_working_context(ctx)
        player = await players.find_one({"user_id": ctx.author.id})
        energy = player.get("stats", {}).get("energy", 0) if player else 0
        
        if energy < 40: return await ctx.send(f"❌ Heists require 40⚡!")

        # Success rate for heist is naturally lower in code logic
        success = await self.mg_manager.run(ctx, "memory") 

        if success and random.random() < 0.60: # 60% chance of actually getting the money even if game won
            loot = random.randint(5000, 15000)
            await players.update_one(
                {"user_id": ctx.author.id}, 
                {"$inc": {"bank": loot, "stats.reputation": -50, "stats.energy": -40}}
            )
            await ctx.send(f"🏦 **HEIST SUCCESS!** You cleaned out **${loot}**! (-40⚡)")
        else:
            # Developer Suggestion: Lose a percentage of bank balance for failed heist
            await players.update_one(
                {"user_id": ctx.author.id}, 
                {"$set": {"money": 0}, "$inc": {"stats.reputation": -30, "stats.energy": -10}}
            )
            await ctx.send("🚑 **HEIST FAILED**: SWAT arrived! You lost all your pocket cash and failed the escape.")

    @commands.hybrid_command(name="steal", description="Rob a player (30% Success Rate - 10⚡)")
    @app_commands.describe(target="The player you want to rob")
    async def steal(self, ctx, target: discord.Member):
        if target.id == ctx.author.id:
            return await ctx.send("❌ You can't rob yourself.")

        thief = await players.find_one({"user_id": ctx.author.id})
        victim = await players.find_one({"user_id": target.id})

        if not thief or not victim: return await ctx.send("❌ Profile not found!")
        
        energy = thief.get("stats", {}).get("energy", 0)
        if energy < 10: return await ctx.send(f"❌ Need 10⚡!")

        # LIMIT: You cannot steal from someone with less than $500 (Newbie protection)
        if victim.get("money", 0) < 500:
            return await ctx.send("❌ This target is under protection (Less than $500).")

        # CHANCE SYSTEM: 30% Base Success, modified by your Dexterity
        dex = thief.get("stats", {}).get("dexterity", 3)
        chance = 0.30 + (dex * 0.01) # Every point of dex adds 1%
        
        if random.random() < chance:
            # LIMIT: Cannot steal more than 70% of target cash
            max_steal = int(victim["money"] * 0.70)
            stolen = random.randint(int(victim["money"] * 0.10), max_steal)
            
            await players.update_one({"user_id": ctx.author.id}, {"$inc": {"money": stolen, "stats.energy": -10}})
            await players.update_one({"user_id": target.id}, {"$inc": {"money": -stolen}})
            await ctx.send(f"🧤 **Success!** You masterfully stole **${stolen}** from {target.mention}! (-10⚡)")
        else:
            # Developer Suggestion: When you fail a steal, the target gets some of your money!
            fine = 250
            await players.update_one({"user_id": ctx.author.id}, {"$inc": {"money": -fine, "stats.energy": -5}})
            await players.update_one({"user_id": target.id}, {"$inc": {"money": 100}}) # Reward victim for catching them
            await ctx.send(f"🚨 **Busted!** {target.mention} caught you. You were fined **$250**.")

async def setup(bot):
    await bot.add_cog(Crime(bot))
