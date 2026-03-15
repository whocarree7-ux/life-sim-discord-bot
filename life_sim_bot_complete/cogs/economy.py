import discord
from discord.ext import commands, tasks
from database.db import players

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.add_interest.start()

    def cog_unload(self):
        self.add_interest.cancel()

    @tasks.loop(hours=24)
    async def add_interest(self):
        """Adds 1% interest to everyone's bank balance daily."""
        interest_rate = 0.01 
        await players.update_many(
            {"bank": {"$gt": 0}}, 
            [{"$set": {"bank": {"$add": ["$bank", {"$multiply": ["$bank", interest_rate]}]}}}]
        )
        print("💰 Daily interest distributed.")

    @commands.command(aliases=["dep"])
    async def deposit(self, ctx, amount: str):
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

    @commands.command()
    async def loan(self, ctx, amount: int):
        """Take a loan from the bank with a 5% interest fee."""
        if amount <= 0: return await ctx.send("❌ You can't borrow nothing!")
        if amount > 5000: return await ctx.send("❌ The bank won't trust you with more than $5000!")
        
        player = await players.find_one({"user_id": ctx.author.id})
        if not player: return await ctx.send("❌ Use `!start` first!")
        
        if player.get("debt", 0) > 0:
            return await ctx.send("❌ **Access Denied:** You must pay off your current loan before taking another!")

        # Calculate debt (Loan + 5% fee)
        total_debt = int(amount * 1.05)
        
        await players.update_one(
            {"user_id": ctx.author.id},
            {"$inc": {"bank": amount, "debt": total_debt}}
        )

        # Modern Embed for the Loan
        embed = discord.Embed(title="🏦 Bank of Arcadia: Loan Approved", color=discord.Color.gold())
        embed.add_field(name="Amount Received", value=f"💰 ${amount}", inline=True)
        embed.add_field(name="Total Debt", value=f"📉 ${total_debt}", inline=True)
        embed.set_footer(text="Your debt will be cleared as you pay it back.")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
    
