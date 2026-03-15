import discord
from discord.ext import commands
import json
from database.db import players
from systems.minigame_manager import MinigameManager

class Jobs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mg_manager = MinigameManager() # Initialize the manager
        try:
            with open("assets/jobs.json") as f:
                self.jobs = json.load(f)
        except:
            self.jobs = [{"name": "laborer", "salary": 30, "req_rep": 0, "minigame": "random"}]

    @commands.command()
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def work(self, ctx):
        player = await players.find_one({"user_id": ctx.author.id})
        
        if not player:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Use `!start` first.")

        # Identify current job and the associated minigame
        job_id = player.get("job", "laborer")
        job_data = next((j for j in self.jobs if j["name"] == job_id), self.jobs[0])

        target_game = job_data.get("minigame", "random")
        
        await ctx.send(f"⚒️ **Work Shift:** Preparing your task for **{job_data['name'].replace('_', ' ').title()}**...")

        # --- Trigger the manager ---
        success = await self.mg_manager.run(ctx, target_game)

        if success:
            salary = job_data["salary"]
            # Reward money and reputation
            await players.update_one(
                {"user_id": ctx.author.id},
                {"$inc": {"money": salary, "stats.reputation": 5}}
            )
            await ctx.send(f"✅ **Shift Complete!** You earned **${salary}** and **+5 Rep**.")
        else:
            await ctx.send(f"❌ **Shift Failed!** Better luck next time.")

async def setup(bot):
    await bot.add_cog(Jobs(bot))
    
