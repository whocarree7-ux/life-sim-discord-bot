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

    async def get_working_context(self, ctx):
        if ctx.interaction:
            if not ctx.interaction.response.is_done():
                await ctx.interaction.response.defer()
            ctx.send = ctx.interaction.followup.send
        return ctx

    async def check_jail(self, ctx, player):
        jail_until = player.get("jail_until", 0)
        if time.time() < jail_until:
            remaining = int((jail_until - time.time()) / 60)
            if remaining < 1: remaining = 1
            await ctx.send(f"🚫 **JAIL**: You are locked up for another **{remaining}m**. You can't commit crimes yet!")
            return True
        return False

    @commands.hybrid_command(name="crime", description="Commit a random crime (15⚡)")
    @commands.cooldown(1, 30, commands.BucketType.user) # 30 second cooldown
    async def crime(self, ctx):
        ctx = await self.get_working_context(ctx)
        player = await players.find_one({"user_id": ctx.author.id})
        if not player: return await ctx.send("❌ Start your life first!")
        if await self.check_jail(ctx, player): return

        energy = player.get("stats", {}).get("energy", 0)
        if energy < 15: return await ctx.send(f"❌ Too tired! ({energy}/15⚡)")

        success = await self.mg_manager.run(ctx, "typing") 
        scenario = get_random_crime()

        if success:
            if random.random() < 0.10:
                return await ctx.send("🕵️ The police were watching! You had to ditch the loot and run.")

            # SCALING: Base loot + (Reputation factor for veterans)
            rep = abs(player.get("stats", {}).get("reputation", 0))
            base_loot = random.randint(scenario['min_loot'], scenario['max_loot'])
            scaling_bonus = int(rep * 0.5) # Veterans get bonus based on "experience" (rep)
            loot = base_loot + scaling_bonus

            await players.update_one(
                {"user_id": ctx.author.id}, 
                {"$inc": {"money": loot, "stats.reputation": scenario['rep_loss'], "stats.energy": -15}}
            )
            await ctx.send(f"✅ **{scenario['name']}**: {scenario['desc']}\nEarned **${loot}**! (-15⚡)")
        else:
            await players.update_one(
                {"user_id": ctx.author.id}, 
                {"$inc": {"money": -scenario['penalty'], "stats.reputation": scenario['rep_loss'], "stats.energy": -5}}
            )
            await ctx.send(f"👮 **Busted**: Fined **${scenario['penalty']}**.")

    @commands.hybrid_command(name="heist", description="High-stakes bank robbery (40⚡)")
    @commands.cooldown(1, 3600, commands.BucketType.user) # 1 hour cooldown
    async def heist(self, ctx):
        ctx = await self.get_working_context(ctx)
        player = await players.find_one({"user_id": ctx.author.id})
        if not player: return await ctx.send("❌ Start your life first!")
        if await self.check_jail(ctx, player): return
        
        energy = player.get("stats", {}).get("energy", 0)
        if energy < 40: return await ctx.send(f"❌ Heists require 40⚡!")

        success = await self.mg_manager.run(ctx, "memory") 

        if success and random.random() < 0.50:
            # SCALING: Large bonus for intelligence in heists
            intel = player.get('stats', {}).get('intelligence', 0)
            loot = random.randint(5000, 15000) + (intel * 50)
            
            await players.update_one(
                {"user_id": ctx.author.id}, 
                {"$inc": {"bank": loot, "stats.reputation": -50, "stats.energy": -40}}
            )
            await ctx.send(f"🏦 **HEIST SUCCESS!** You cleaned out **${loot}**! (-40⚡)")
        else:
            jail_time = time.time() + 600 
            await players.update_one(
                {"user_id": ctx.author.id}, 
                {"$set": {"money": 0, "jail_until": jail_time}, "$inc": {"stats.reputation": -30, "stats.energy": -10}}
            )
            await ctx.send("🚑 **HEIST FAILED**: SWAT arrived! You lost all pocket cash and were sent to **Jail (10m)**.")

    @commands.hybrid_command(name="hack", description="Hack the mainframe (20⚡)")
    @commands.cooldown(1, 300, commands.BucketType.user) # 5 minute cooldown
    async def hack(self, ctx):
        ctx = await self.get_working_context(ctx)
        player = await players.find_one({"user_id": ctx.author.id})
        if not player: return await ctx.send("❌ Start your life first!")
        if await self.check_jail(ctx, player): return

        energy = player.get("stats", {}).get("energy", 0)
        if energy < 20: return await ctx.send(f"❌ Need 20⚡ to hack!")

        success = await self.mg_manager.run(ctx, "reaction") 

        if success:
            # SCALING: Intelligence-heavy reward with high variance (randomness)
            intel = player.get('stats', {}).get('intelligence', 0)
            base_reward = random.randint(800, 1500)
            intel_bonus = int(intel * random.uniform(15, 25)) # Random multiplier for stats
            reward = base_reward + intel_bonus
            
            await players.update_one(
                {"user_id": ctx.author.id}, 
                {"$inc": {"money": reward, "stats.energy": -20}}
            )
            await ctx.send(f"💻 **HACKED**: Redirected **${reward}**. (-20⚡)")
        else:
            await players.update_one({"user_id": ctx.author.id}, {"$inc": {"stats.energy": -5}})
            await ctx.send("🚨 Trace detected! Connection terminated. (-5⚡)")

    @commands.hybrid_command(name="steal", description="Rob a player (10⚡)")
    @app_commands.describe(target="The player you want to rob")
    async def steal(self, ctx, target: discord.Member):
        if target.id == ctx.author.id: return await ctx.send("❌ You can't rob yourself.")
        ctx = await self.get_working_context(ctx)

        thief = await players.find_one({"user_id": ctx.author.id})
        victim = await players.find_one({"user_id": target.id})

        if not thief or not victim: return await ctx.send("❌ Profile not found!")
        if await self.check_jail(ctx, thief): return
        
        energy = thief.get("stats", {}).get("energy", 0)
        if energy < 10: return await ctx.send(f"❌ Need 10⚡!")

        if victim.get("money", 0) < 500:
            return await ctx.send("❌ This target is too poor to rob ($500 minimum).")

        dex = thief.get("stats", {}).get("dexterity", 3)
        chance = 0.30 + (dex * 0.02)
        
        if random.random() < chance:
            max_steal = int(victim["money"] * 0.70)
            stolen = random.randint(int(victim["money"] * 0.05), max_steal)
            
            await players.update_one({"user_id": ctx.author.id}, {"$inc": {"money": stolen, "stats.energy": -10}})
            await players.update_one({"user_id": target.id}, {"$inc": {"money": -stolen}})
            await ctx.send(f"🧤 **Success!** You stole **${stolen}** from {target.mention}! (-10⚡)")
        else:
            fine = 200
            await players.update_one({"user_id": ctx.author.id}, {"$inc": {"money": -fine, "stats.energy": -5}})
            await players.update_one({"user_id": target.id}, {"$inc": {"money": 100}})
            await ctx.send(f"🚨 **Busted!** You were caught and fined **${fine}**. {target.mention} kept some for themselves!")

    # Error handler for cooldowns
    @crime.error
    @heist.error
    @hack.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ **Cooldown**: Try again in {int(error.retry_after)}s", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Crime(bot))
