import discord
from discord.ext import commands, tasks
from discord import app_commands
from database.db import players

class Economy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.add_interest.start()
        self.collect_debt.start()

    def cog_unload(self):
        self.add_interest.cancel()
        self.collect_debt.cancel()

    # -----------------------------
    # DAILY BANK INTEREST
    # -----------------------------
    @tasks.loop(hours=24)
    async def add_interest(self):
        interest_rate = 0.01
        await players.update_many(
            {"bank": {"$gt": 0}},
            [{"$set": {"bank": {"$add": ["$bank", {"$multiply": ["$bank", interest_rate]}]}}}]
        )
        await players.update_many(
            {"bank": {"$gte": 1000}, "debt": 0},
            {"$inc": {"credit_score": 5}}
        )
        print("💰 Interest distributed.")

    # -----------------------------
    # AUTOMATIC DEBT COLLECTION
    # -----------------------------
    @tasks.loop(hours=24)
    async def collect_debt(self):
        all_players = players.find({"debt": {"$gt": 0}})
        async for player in all_players:
            user_id = player["user_id"]
            debt = player["debt"]
            bank = player.get("bank", 0)
            if bank > 0:
                payment = min(bank, debt)
                await players.update_one(
                    {"user_id": user_id},
                    {"$inc": {"bank": -payment, "debt": -payment}}
                )

    # -----------------------------
    # /bank or !bank
    # -----------------------------
    @commands.hybrid_command(name="bank", description="View your banking information")
    async def bank(self, ctx: commands.Context):
        player = await players.find_one({"user_id": ctx.author.id})
        if not player:
            return await ctx.send("❌ Use `/start` first")

        embed = discord.Embed(title="🏦 Arcadia Bank", color=discord.Color.blue())
        embed.add_field(name="Bank Balance", value=f"${player.get('bank', 0)}")
        embed.add_field(name="Debt", value=f"${player.get('debt', 0)}")
        embed.add_field(name="Credit Score", value=f"{player.get('credit_score', 500)}")
        await ctx.send(embed=embed)

    # -----------------------------
    # /deposit or !deposit
    # -----------------------------
    @commands.hybrid_command(name="deposit", description="Deposit money into the bank")
    async def deposit(self, ctx: commands.Context, amount: int):
        player = await players.find_one({"user_id": ctx.author.id})
        if not player:
            return await ctx.send("❌ Use `/start` first")

        cash = player.get("money", 0)
        if amount > cash:
            return await ctx.send("❌ Not enough wallet money")

        await players.update_one(
            {"user_id": ctx.author.id},
            {"$inc": {"money": -amount, "bank": amount}}
        )
        await ctx.send(f"✅ Deposited **${amount}**")

    # -----------------------------
    # /withdraw or !withdraw
    # -----------------------------
    @commands.hybrid_command(name="withdraw", description="Withdraw money from the bank")
    async def withdraw(self, ctx: commands.Context, amount: int):
        player = await players.find_one({"user_id": ctx.author.id})
        bank = player.get("bank", 0)
        if amount > bank:
            return await ctx.send("❌ Not enough bank balance")

        await players.update_one(
            {"user_id": ctx.author.id},
            {"$inc": {"money": amount, "bank": -amount}}
        )
        await ctx.send(f"🏧 Withdrew **${amount}**")

    # -----------------------------
    # /loan or !loan
    # -----------------------------
    @commands.hybrid_command(name="loan", description="Take a loan from the bank")
    async def loan(self, ctx: commands.Context, amount: int):
        player = await players.find_one({"user_id": ctx.author.id})
        if not player:
            return await ctx.send("❌ Use `/start` first")

        credit = player.get("credit_score", 500)
        if credit < 300:
            return await ctx.send("❌ Credit score too low")

        total_debt = int(amount * 1.05)
        await players.update_one(
            {"user_id": ctx.author.id},
            {"$inc": {"bank": amount, "debt": total_debt}}
        )

        embed = discord.Embed(title="🏦 Loan Approved", color=discord.Color.gold())
        embed.add_field(name="Received", value=f"${amount}")
        embed.add_field(name="Total Debt", value=f"${total_debt}")
        await ctx.send(embed=embed)

    # -----------------------------
    # /repay or !repay
    # -----------------------------
    @commands.hybrid_command(name="repay", description="Repay your loan debt")
    async def repay(self, ctx: commands.Context, amount: int):
        player = await players.find_one({"user_id": ctx.author.id})
        if not player:
            return await ctx.send("❌ Use `/start` first")

        debt = player.get("debt", 0)
        bank = player.get("bank", 0)
        if debt <= 0:
            return await ctx.send("✅ You have no debt")
        if amount > bank:
            return await ctx.send("❌ Not enough money in bank")

        if amount > debt:
            amount = debt

        await players.update_one(
            {"user_id": ctx.author.id},
            {"$inc": {"bank": -amount, "debt": -amount}}
        )

        embed = discord.Embed(title="🏦 Loan Repayment", color=discord.Color.green())
        embed.add_field(name="Paid", value=f"${amount}")
        embed.add_field(name="Remaining Debt", value=f"${debt - amount}")
        await ctx.send(embed=embed)

    # -----------------------------
    # /pay or !pay
    # -----------------------------
    @commands.hybrid_command(name="pay", description="Transfer money from your bank to another player")
    @app_commands.describe(member="The player you want to pay", amount="Amount to send")
    async def pay(self, ctx: commands.Context, member: discord.Member, amount: int):
        if amount <= 0:
            return await ctx.send("❌ Amount must be greater than 0.")
        if member.id == ctx.author.id:
            return await ctx.send("❌ You cannot pay yourself!")
        if member.bot:
            return await ctx.send("❌ You cannot pay bots.")

        sender = await players.find_one({"user_id": ctx.author.id})
        if not sender:
            return await ctx.send("❌ Use `/start` first.")

        sender_bank = sender.get("bank", 0)
        if amount > sender_bank:
            return await ctx.send(f"❌ You don't have enough money in your bank!")

        receiver = await players.find_one({"user_id": member.id})
        if not receiver:
            return await ctx.send(f"❌ {member.display_name} hasn't started their journey yet!")

        tax = int(amount * 0.05)
        final_amount = amount - tax

        await players.update_one({"user_id": ctx.author.id}, {"$inc": {"bank": -amount}})
        await players.update_one({"user_id": member.id}, {"$inc": {"bank": final_amount}})

        embed = discord.Embed(title="💸 Wire Transfer Complete", color=discord.Color.green())
        embed.add_field(name="Sender", value=ctx.author.mention, inline=True)
        embed.add_field(name="Receiver", value=member.mention, inline=True)
        embed.add_field(name="Sent", value=f"${amount}", inline=True)
        embed.add_field(name="Tax (5%)", value=f"-${tax}", inline=True)
        embed.add_field(name="Received", value=f"**${final_amount}**", inline=True)
        
        await ctx.send(content=member.mention, embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
