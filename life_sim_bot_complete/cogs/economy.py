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
    # /bank
    # -----------------------------
    @app_commands.command(name="bank", description="View your banking information")
    async def bank(self, interaction: discord.Interaction):
        player = await players.find_one({"user_id": interaction.user.id})
        if not player:
            return await interaction.response.send_message("❌ Use `/start` first")

        embed = discord.Embed(title="🏦 Arcadia Bank", color=discord.Color.blue())
        embed.add_field(name="Bank Balance", value=f"${player.get('bank', 0)}")
        embed.add_field(name="Debt", value=f"${player.get('debt', 0)}")
        embed.add_field(name="Credit Score", value=f"{player.get('credit_score', 500)}")

        await interaction.response.send_message(embed=embed)

    # -----------------------------
    # /deposit
    # -----------------------------
    @app_commands.command(name="deposit", description="Deposit money into the bank")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        player = await players.find_one({"user_id": interaction.user.id})
        if not player:
            return await interaction.response.send_message("❌ Use `/start` first")

        cash = player.get("money", 0)
        if amount > cash:
            return await interaction.response.send_message("❌ Not enough wallet money")

        await players.update_one(
            {"user_id": interaction.user.id},
            {"$inc": {"money": -amount, "bank": amount}}
        )
        await interaction.response.send_message(f"✅ Deposited **${amount}**")

    # -----------------------------
    # /withdraw
    # -----------------------------
    @app_commands.command(name="withdraw", description="Withdraw money from the bank")
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        player = await players.find_one({"user_id": interaction.user.id})
        bank = player.get("bank", 0)
        if amount > bank:
            return await interaction.response.send_message("❌ Not enough bank balance")

        await players.update_one(
            {"user_id": interaction.user.id},
            {"$inc": {"money": amount, "bank": -amount}}
        )
        await interaction.response.send_message(f"🏧 Withdrew **${amount}**")

    # -----------------------------
    # /loan
    # -----------------------------
    @app_commands.command(name="loan", description="Take a loan from the bank")
    async def loan(self, interaction: discord.Interaction, amount: int):
        player = await players.find_one({"user_id": interaction.user.id})
        if not player:
            return await interaction.response.send_message("❌ Use `/start` first")

        credit = player.get("credit_score", 500)
        if credit < 300:
            return await interaction.response.send_message("❌ Credit score too low")

        total_debt = int(amount * 1.05)
        await players.update_one(
            {"user_id": interaction.user.id},
            {"$inc": {"bank": amount, "debt": total_debt}}
        )

        embed = discord.Embed(title="🏦 Loan Approved", color=discord.Color.gold())
        embed.add_field(name="Received", value=f"${amount}")
        embed.add_field(name="Total Debt", value=f"${total_debt}")
        await interaction.response.send_message(embed=embed)

    # -----------------------------
    # /repay
    # -----------------------------
    @app_commands.command(name="repay", description="Repay your loan debt")
    async def repay(self, interaction: discord.Interaction, amount: int):
        player = await players.find_one({"user_id": interaction.user.id})
        if not player:
            return await interaction.response.send_message("❌ Use `/start` first")

        debt = player.get("debt", 0)
        bank = player.get("bank", 0)

        if debt <= 0:
            return await interaction.response.send_message("✅ You have no debt")
        if amount > bank:
            return await interaction.response.send_message("❌ Not enough money in bank")

        if amount > debt:
            amount = debt

        await players.update_one(
            {"user_id": interaction.user.id},
            {"$inc": {"bank": -amount, "debt": -amount}}
        )

        embed = discord.Embed(title="🏦 Loan Repayment", color=discord.Color.green())
        embed.add_field(name="Paid", value=f"${amount}")
        embed.add_field(name="Remaining Debt", value=f"${debt - amount}")
        await interaction.response.send_message(embed=embed)

    # -----------------------------
    # /pay
    # -----------------------------
    @app_commands.command(name="pay", description="Transfer money from your bank to another player")
    @app_commands.describe(member="The player you want to pay", amount="Amount to send")
    async def pay(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        # 1. Basic Checks
        if amount <= 0:
            return await interaction.response.send_message("❌ Amount must be greater than 0.", ephemeral=True)
        
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ You cannot pay yourself!", ephemeral=True)

        if member.bot:
            return await interaction.response.send_message("❌ You cannot pay bots.", ephemeral=True)

        # 2. Fetch Sender Data
        sender = await players.find_one({"user_id": interaction.user.id})
        if not sender:
            return await interaction.response.send_message("❌ Use `/start` first.", ephemeral=True)

        sender_bank = sender.get("bank", 0)

        # 3. Check Balance
        if amount > sender_bank:
            return await interaction.response.send_message(
                f"❌ You don't have enough money in your bank! (Current Balance: **${sender_bank}**)", 
                ephemeral=True
            )

        # 4. Fetch Receiver Data
        receiver = await players.find_one({"user_id": member.id})
        if not receiver:
            return await interaction.response.send_message(f"❌ {member.display_name} hasn't started their journey yet!", ephemeral=True)

        # 5. Process Transaction with Tax
        tax = int(amount * 0.05)
        final_amount = amount - tax

        # Deduct full amount from Sender
        await players.update_one(
            {"user_id": interaction.user.id},
            {"$inc": {"bank": -amount}}
        )

        # Add taxed amount to Receiver
        await players.update_one(
            {"user_id": member.id},
            {"$inc": {"bank": final_amount}}
        )

        # 6. Send Confirmation Embed
        embed = discord.Embed(
            title="💸 Wire Transfer Complete",
            description=f"Successfully transferred funds to **{member.display_name}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Sender", value=interaction.user.mention, inline=True)
        embed.add_field(name="Receiver", value=member.mention, inline=True)
        embed.add_field(name="Amount Sent", value=f"${amount}", inline=True)
        embed.add_field(name="Tax (5%)", value=f"-${tax}", inline=True)
        embed.add_field(name="Final Received", value=f"**${final_amount}**", inline=True)
        embed.set_footer(text="Arcadia Banking System • Transaction Tax Applied")

        await interaction.response.send_message(content=member.mention, embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
