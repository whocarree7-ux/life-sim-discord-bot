
import discord
from discord.ext import commands
import json
from database.db import players
import random

class Jobs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("assets/jobs.json") as f:
            self.jobs = json.load(f)

    @commands.command()
    async def jobs(self, ctx):
        msg = "Available Jobs:\n"
        for j in self.jobs:
            msg += f"{j['name']} - ${j['salary']}\n"
        await ctx.send(msg)

    @commands.command()
    async def work(self, ctx):
        player = await players.find_one({"user_id": ctx.author.id})

        if not player:
            await ctx.send("Create profile first with !start")
            return

        job = random.choice(self.jobs)
        salary = job["salary"]

        await players.update_one(
            {"user_id": ctx.author.id},
            {"$inc": {"money": salary}}
        )

        await ctx.send(f"You worked as **{job['name']}** and earned **${salary}**")

async def setup(bot):
    await bot.add_cog(Jobs(bot))
