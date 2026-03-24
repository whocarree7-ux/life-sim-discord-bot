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
        """
        This helper ensures that if it's a Slash Command, 
        the minigame gets a '.send()' method to avoid the error you saw.
        """
        if ctx.interaction:
            # If slash command, we defer so the game has time to load
            if not ctx.interaction.response.is_done():
                await ctx.interaction.response.defer()
            # We return ctx, but ensure .send works by mapping it to followup.send
            ctx.send = ctx.interaction.followup.send
        return ctx

    @commands.hybrid_command(name="crime", description="Commit a random crime (15⚡)")
    async def crime(self, ctx):
        ctx = await self.get_working_context(ctx)
        
        player = await players.find_one({"user_id": ctx.author.id})
        if not player: return await ctx.send("❌ Start your life first!")
        
        energy = player.get("stats", {}).get("energy", 0)
        if energy < 15: return await ctx.send(f"❌ Too tired! ({energy}/15⚡)")

        # Run the game - Passing 'ctx' which now always has '.send()'
        success = await self.mg_manager.run(ctx, "typing") 
        scenario = get_random_crime()

        if success:
            loot = random.randint(scenario['min_loot'], scenario['max_loot'])
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
            await ctx.send(f"👮 **Busted**: You paid a **${scenario['penalty']}** fine.")

    @commands.hybrid_command(name="heist", description="High-stakes bank robbery (40⚡)")
    async def heist(self, ctx):
        ctx = await self.get_working_context(ctx)
        
        player = await players.find_one({"user_id": ctx.author.id})
        energy = player.get("stats", {}).get("energy", 0) if player else 0
        
        if energy < 40: return await ctx.send(f"❌ Heists require 40⚡!")

        success = await self.mg_manager.run(ctx, "memory") 

        if success:
            loot = random.randint(5000, 15000)
            await players.update_one(
                {"user_id": ctx.author.id}, 
                {"$inc": {"bank": loot, "stats.reputation": -50, "stats.energy": -40}}
            )
            await ctx.send(f"🏦 **HEIST SUCCESS!** You cleaned out **${loot}**! (-40⚡)")
        else:
            await players.update_one(
                {"user_id": ctx.author.id}, 
                {"$set": {"money": 0}, "$inc": {"stats.reputation": -30, "stats.energy": -10}}
            )
            await ctx.send("🚑 **HEIST FAILED**: Lost all pocket cash and 10⚡.")

    @commands.hybrid_command(name="hack", description="Hack the mainframe (20⚡)")
    async def hack(self, ctx):
        ctx = await self.get_working_context(ctx)

        player = await players.find_one({"user_id": ctx.author.id})
        if not player: return await ctx.send("❌ Start your life first!")
        
        energy = player.get("stats", {}).get("energy", 0)
        if energy < 20: return await ctx.send(f"❌ Need 20⚡ to hack!")

        success = await self.mg_manager.run(ctx, "reaction") 

        if success:
            intel = player.get('stats', {}).get('intelligence', 0)
            reward = 1000 + (intel * 10)
            await players.update_one(
                {"user_id": ctx.author.id}, 
                {"$inc": {"money": reward, "stats.energy": -20}}
            )
            await ctx.send(f"💻 **HACKED**: Redirected **${reward}**. (-20⚡)")
        else:
            await players.update_one({"user_id": ctx.author.id}, {"$inc": {"stats.energy": -5}})
            await ctx.send("🚨 Trace detected! Connection terminated.")

    @commands.hybrid_command(name="steal", description="Rob a player (10⚡)")
    @app_commands.describe(target="The player you want to rob")
    async def steal(self, ctx, target: discord.Member):
        if target.id == ctx.author.id:
            return await ctx.send("❌ You can't rob yourself.")

        thief = await players.find_one({"user_id": ctx.author.id})
        victim = await players.find_one({"user_id": target.id})

        if not thief or not victim:
            return await ctx.send("❌ Profile not found!")
        
        energy = thief.get("stats", {}).get("energy", 0)
        if energy < 10: return await ctx.send(f"❌ Need 10⚡!")

        if victim.get("money", 0) < 100:
            return await ctx.send("❌ Target is too poor.")

        chance = calculate_steal_chance(thief.get('stats', {}), victim.get('stats', {}))
        
        if random.random() < chance:
            stolen = int(victim["money"] * random.uniform(0.1, 0.25))
            await players.update_one({"user_id": ctx.author.id}, {"$inc": {"money": stolen, "stats.energy": -10}})
            await players.update_one({"user_id": target.id}, {"$inc": {"money": -stolen}})
            await ctx.send(f"🧤 **Success!** Stole **${stolen}** from {target.mention}!")
        else:
            await players.update_one({"user_id": ctx.author.id}, {"$inc": {"money": -150, "stats.energy": -5}})
            await ctx.send(f"🚨 **Busted!** You lost **$150** while fleeing.")

async def setup(bot):
    await bot.add_cog(Crime(bot))
