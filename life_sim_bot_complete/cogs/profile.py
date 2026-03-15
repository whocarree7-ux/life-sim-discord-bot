
import discord
from discord.ext import commands
import random
import json
from database.db import players
from database.models import default_player

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("assets/backgrounds.json") as f:
            self.backgrounds = json.load(f)

    @commands.command()
    async def start(self, ctx):
        existing = await players.find_one({"user_id": ctx.author.id})
        if existing:
            await ctx.send("You already have a profile.")
            return

        background = random.choice(self.backgrounds)
        player = default_player(ctx.author.id, background)

        await players.insert_one(player)

        await ctx.send(f"You started life as **{background['name']}** with ${background['money']}")

    @commands.command()
    async def profile(self, ctx):
        player = await players.find_one({"user_id": ctx.author.id})

        if not player:
            await ctx.send("Use !start first.")
            return

        embed = discord.Embed(title=f"{ctx.author.name}'s Life")

        embed.add_field(name="Money", value=player["money"])
        embed.add_field(name="Job", value=player["job"])
        embed.add_field(name="House", value=player["house"])

        stats = player["stats"]

        for k,v in stats.items():
            embed.add_field(name=k.capitalize(), value=v)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Profile(bot))
