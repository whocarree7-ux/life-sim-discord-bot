import discord
from discord.ext import commands
import json
from database.db import players

class Jobs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            with open("assets/jobs.json") as f:
                self.jobs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.jobs = [{"name": "Unemployed", "salary": 20, "req_rep": 0}]

    @commands.command(name="jobs")
    async def list_jobs(self, ctx):
        """Displays jobs and their reputation requirements."""
        player = await players.find_one({"user_id": ctx.author.id})
        user_rep = player.get("stats", {}).get("reputation", 0) if player else 0

        embed = discord.Embed(title="💼 Job Board", color=discord.Color.gold())
        embed.set_footer(text=f"Your Reputation: {user_rep}")

        for j in self.jobs:
            status = "✅ Available" if user_rep >= j['req_rep'] else f"🔒 Needs {j['req_rep']} Rep"
            embed.add_field(
                name=f"{j['name'].replace('_', ' ').title()}",
                value=f"Salary: `${j['salary']}`\nStatus: {status}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def apply(self, ctx, *, job_name: str):
        """Apply for a specific job."""
        job_name = job_name.lower().replace(" ", "_")
        job = next((j for j in self.jobs if j["name"] == job_name), None)

        if not job:
            return await ctx.send("❌ That job doesn't exist!")

        player = await players.find_one({"user_id": ctx.author.id})
        if not player:
            return await ctx.send("❌ Use `!start` first.")

        user_rep = player.get("stats", {}).get("reputation", 0)

        if user_rep < job["req_rep"]:
            return await ctx.send(f"🚫 You need **{job['req_rep']} reputation** for this job!")

        await players.update_one(
            {"user_id": ctx.author.id},
            {"$set": {"job": job["name"]}}
        )
        await ctx.send(f"💼 Congrats! You are now a **{job['name'].replace('_', ' ').title()}**.")

    @commands.command()
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def work(self, ctx):
        """Work at your current job."""
        player = await players.find_one({"user_id": ctx.author.id})
        
        if not player:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Use `!start` first.")

        job_id = player.get("job", "unemployed")
        # Find the job details from our list
        job_data = next((j for j in self.jobs if j["name"] == job_id), None)
        
        if not job_data:
            # If their job isn't in the list anymore, give them base pay
            job_data = {"name": "Odd Jobs", "salary": 30}

        salary = job_data["salary"]
        
        # We add money AND a little bit of reputation for working!
        await players.update_one(
            {"user_id": ctx.author.id},
            {"$inc": {"money": salary, "stats.reputation": 5}} 
        )

        await ctx.send(f"✅ You worked as a **{job_data['name'].replace('_', ' ').title()}** and earned **${salary}** (+5 Rep)!")

    @work.error
    async def work_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Too tired! Try again in {round(error.retry_after/60)} minutes.")

async def setup(bot):
    await bot.add_cog(Jobs(bot))
        
