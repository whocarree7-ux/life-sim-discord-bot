
import discord
from discord.ext import commands
from database.db import players

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def balance(self, ctx):
        player = await players.find_one({"user_id": ctx.author.id})
        if not player:
            await ctx.send("Use !start first")
            return

        await ctx.send(f"Balance: ${player['money']}")

async def setup(bot):
    await bot.add_cog(Economy(bot))
