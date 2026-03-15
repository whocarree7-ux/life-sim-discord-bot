import discord
from discord.ext import commands
import json
import random
from database.db import players

class Jobs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            with open("assets/jobs.json") as f:
                self.jobs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.jobs = [{"name": "Laborer", "salary": 50}] # Fallback

    @commands.command(name="jobs")
    async def list_jobs(self, ctx):
        """Displays all available jobs in a clean embed."""
        embed = discord.Embed(title="💼 Available Jobs", color=discord.Color.blue())
        
        description = ""
        for j in self.jobs:
            description += f"**{j['name']}** — `${j['salary']}`\n"
        
        embed.description = description
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 3600, commands.BucketType.user) # 1 use per hour
    async def work(self, ctx):
        """Earn money by working a random job."""
        job = random.choice(self.jobs)
        salary = job["salary"]

        # Use find_one_and_update to do everything in one database hit
        result = await players.find_one_and_update(
            {"user_id": ctx.author.id},
            {"$inc": {"money": salary}},
            upsert=False # Don't create a profile if it doesn't exist
        )

        if not result:
            # Manually reset cooldown so they don't lose their turn if they forgot to !start
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Create a profile first with `!start`")

        await ctx.send(f"✅ You worked as a **{job['name']}** and earned **${salary}**!")

    @work.error
    async def work_error(self, ctx, error):
        """Handles cooldown errors gracefully."""
        if isinstance(error, commands.CommandOnCooldown):
            seconds = round(error.retry_after)
            await ctx.send(f"⏳ Chill! You can work again in **{seconds // 60}m {seconds % 60}s**.", delete_after=10)

async def setup(bot):
    await bot.add_cog(Jobs(bot))
    
