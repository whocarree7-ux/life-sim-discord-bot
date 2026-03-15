import discord
from discord.ext import commands, tasks
from database.db import players

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.add_interest.start()
        self.collect_debt.start()

    def cog_unload(self):
        self.add_interest.cancel()
        self.collect_debt.cancel()

    @tasks.loop(hours=24)
    async def add_interest(self):
        """Adds 1% interest to everyone's bank balance daily."""
        interest_rate = 0.01 
        await players.update_many(
            {"bank": {"$gt": 0}}, 
            [{"$set": {"bank": {"$add": ["$bank", {"$multiply": ["$bank", interest_rate]}]}}}]
        )
        print("💰 Daily interest distributed.")

    @tasks.loop(hours=24)
    async def collect_debt(self):
        """Deducts debt, lowers credit scores, and seizes wallet cash after 3 days."""
        all_players = players.find({"debt": {"$gt": 0}})
        
        async for player in all_players:
            user_id = player["user_id"]
            debt = player["debt"]
            bank = player.get("bank", 0)
            wallet = player.get("money", 0)
            missed_days = player.get("missed_payments", 0)
            user = self.bot.get_user(user_id)

            if bank > 0:
                payment = min(bank, debt)
                await players.update_one(
                    {"user_id": user_id},
                    {"$inc": {"bank": -payment, "debt": -payment}, "$set": {"missed_payments": 0}}
                )
                if user:
                    try: await user.send(f"🏦 **Bank of Arcadia:** Deducted **${payment}** from your bank. Remaining debt: **${debt - payment}**.")
                    except: pass
            else:
                # No money in bank - increment missed days and drop credit score
                new_missed = missed_days + 1
                await players.update_one(
                    {"user_id": user_id},
                    {"$inc": {"credit_score": -25}, "$set": {"missed_payments": new_missed}}
                )
                
                # SEIZURE MECHANIC: If 3 days missed, take from wallet
                if new_missed >= 3 and wallet > 0:
                    seizure = min(wallet, debt)
                    await players.update_one(
                        {"user_id": user_id},
                        {"$inc": {"money": -seizure, "debt": -seizure}, "$set": {"missed_payments": 0}}
                    )
                    if user:
                        try: await user.send(f"⚠️ **DEBT COLLECTION:** You ignored your debt for 3 days. We have seized **${seizure}** from your wallet.")
                        except: pass
                elif user:
                    try: await user.send(f"⚠️ **Bank Warning:** You have a debt of **${debt}** but your bank is empty! Your credit score has dropped.")
                    except: pass

    @commands.command(aliases=["dep"])
    async def deposit(self, ctx, amount: str):
        player = await players.find_one({"user_id": ctx.author.id})
        if not player: return await ctx.send("❌ Start your life first!")
        cash = player.get("money", 0)
        bank = player.get("bank", 0)
        limit = player.get("bank_limit", 5000)
        if amount.lower() == "all": amount = cash
        else:
            if not amount.isdigit(): return await ctx.send("❌ Enter a valid number.")
            amount = int(amount)
        if amount > cash: return await ctx.send("❌ You don't have that much cash!")
        if bank + amount > limit: return await ctx.send(f"❌ Your bank is full! (Limit: ${limit})")
        await players.update_one({"user_id": ctx.author.id}, {"$inc": {"money": -amount, "bank": amount}})
        await ctx.send(f"🏦 Deposited **${amount}** into your bank account.")

    @commands.command(aliases=["with"])
    async def withdraw(self, ctx, amount: str):
        player = await players.find_one({"user_id": ctx.author.id})
        bank = player.get("bank", 0)
        if amount.lower() == "all": amount = bank
        else:
            if not amount.isdigit(): return await ctx.send("❌ Enter a valid number.")
            amount = int(amount)
        if amount > bank: return await ctx.send("❌ You don't have that much in your bank!")
        await players.update_one({"user_id": ctx.author.id}, {"$inc": {"money": amount, "bank": -amount}})
        await ctx.send(f"🏧 Withdrew **${amount}** from your bank.")

    @commands.command()
    async def loan(self, ctx, amount: int):
        """Take a loan from the bank. Limits based on credit score."""
        player = await players.find_one({"user_id": ctx.author.id})
        if not player: return await ctx.send("❌ Use `!start` first!")
        
        credit = player.get("credit_score", 500)
        if credit < 300: return await ctx.send("❌ **Access Denied:** Your credit score is too low. The bank doesn't trust you!")
        
        if amount <= 0: return await ctx.send("❌ You can't borrow nothing!")
        if amount > 5000: return await ctx.send("❌ The bank won't trust you with more than $5000!")
        
        if player.get("debt", 0) > 0:
            return await ctx.send("❌ **Access Denied:** Pay your current loan first!")

        total_debt = int(amount * 1.05)
        await players.update_one({"user_id": ctx.author.id}, {"$inc": {"bank": amount, "debt": total_debt}})

        embed = discord.Embed(title="🏦 Bank of Arcadia: Loan Approved", color=discord.Color.gold())
        embed.add_field(name="Amount Received", value=f"💰 ${amount}", inline=True)
        embed.add_field(name="Total Debt", value=f"📉 ${total_debt}", inline=True)
        embed.set_footer(text="Keep money in your bank to avoid wallet seizure and credit drops.")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))

    
