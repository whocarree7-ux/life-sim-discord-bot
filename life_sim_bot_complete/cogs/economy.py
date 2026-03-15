import discord
from discord.ext import commands
from database.db import players

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["dep"])
    async def deposit(self, ctx, amount: str):
        """Move money from cash to bank."""
        player = await players.find_one({"user_id": ctx.author.id})
        if not player: return await ctx.send("❌ Start your life first!")

        cash = player.get("money", 0)
        bank = player.get("bank", 0)
        limit = player.get("bank_limit", 5000)

        if amount.lower() == "all":
            amount = cash
        else:
            if not amount.isdigit(): return await ctx.send("❌ Enter a valid number.")
            amount = int(amount)

        if amount > cash: return await ctx.send("❌ You don't have that much cash!")
        if bank + amount > limit: return await ctx.send(f"❌ Your bank is full! (Limit: ${limit})")

        await players.update_one(
            {"user_id": ctx.author.id},
            {"$inc": {"money": -amount, "bank": amount}}
        )
        await ctx.send(f"🏦 Deposited **${amount}** into your bank account.")

    @commands.command(aliases=["with"])
    async def withdraw(self, ctx, amount: str):
        """Move money from bank to cash."""
        player = await players.find_one({"user_id": ctx.author.id})
        bank = player.get("bank", 0)

        if amount.lower() == "all":
            amount = bank
        else:
            if not amount.isdigit(): return await ctx.send("❌ Enter a valid number.")
            amount = int(amount)

        if amount > bank: return await ctx.send("❌ You don't have that much in your bank!")

        await players.update_one(
            {"user_id": ctx.author.id},
            {"$inc": {"money": amount, "bank": -amount}}
        )
        await ctx.send(f"🏧 Withdrew **${amount}** from your bank.")

async def setup(bot):
    await bot.add_cog(Economy(bot))
