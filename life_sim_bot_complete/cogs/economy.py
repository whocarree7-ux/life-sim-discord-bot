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
        """Adds 1% interest and rewards healthy balances."""
        interest_rate = 0.01 
        
        # 1. Distribute Interest
        await players.update_many(
            {"bank": {"$gt": 0}}, 
            [{"$set": {"bank": {"$add": ["$bank", {"$multiply": ["$bank", interest_rate]}]}}}]
        )
        
        # 2. Reward Good Citizens (+5 Credit Score if bank > 1000 and no debt)
        await players.update_many(
            {"bank": {"$gte": 1000}, "debt": 0},
            {"$inc": {"credit_score": 5}}
        )
        print("💰 Interest and Good Citizen bonuses distributed.")

    @tasks.loop(hours=24)
    async def collect_debt(self):
        """Deducts debt, rewards payments, and seizes wallet cash after 3 days."""
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
                # Success! Reward with +10 Credit Score
                await players.update_one(
                    {"user_id": user_id},
                    {
                        "$inc": {"bank": -payment, "debt": -payment, "credit_score": 10}, 
                        "$set": {"missed_payments": 0}
                    }
                )
                if user:
                    try: await user.send(f"🏦 **Bank of Arcadia:** Automatic payment of **${payment}** processed! Your credit score increased. Remaining debt: **${debt - payment}**.")
                    except: pass
            else:
                new_missed = missed_days + 1
                await players.update_one(
                    {"user_id": user_id},
                    {"$inc": {"credit_score": -25}, "$set": {"missed_payments": new_missed}}
                )
                
                if new_missed >= 3 and wallet > 0:
                    seizure = min(wallet, debt)
                    await players.update_one(
                        {"user_id": user_id},
                        {"$inc": {"money": -seizure, "debt": -seizure}, "$set": {"missed_payments": 0}}
                    )
                    if user:
                        try: await user.send(f"⚠️ **COLLECTIONS SEIZURE:** Debt ignored for 3 days. We seized **${seizure}** from your wallet.")
                        except: pass
                elif user:
                    try: await user.send(f"⚠️ **Bank Warning:** Debt of **${debt}** is due! Your bank is empty; credit score dropped. Please deposit cash immediately.")
                    except: pass

    @commands.command(aliases=["dep"])
    async def deposit(self, ctx, amount: str):
        """Secure your cash in the bank to earn interest and pay debts."""
        player = await players.find_one({"user_id": ctx.author.id})
        if not player: return await ctx.send("❌ Start your life first!")
        cash = player.get("money", 0)
        bank = player.get("bank", 0)
        limit = player.get("bank_limit", 5000)
        
        if amount.lower() == "all": amount = cash
        else:
            if not amount.isdigit(): return await ctx.send("❌ Enter a valid amount.")
            amount = int(amount)
            
        if amount > cash: return await ctx.send("❌ Not enough cash in your wallet!")
        if bank + amount > limit: return await ctx.send(f"❌ Bank capacity full! (Limit: ${limit})")
        
        await players.update_one({"user_id": ctx.author.id}, {"$inc": {"money": -amount, "bank": amount}})
        await ctx.send(f"✅ **Deposit Successful:** ${amount} secured in your vault.")

    @commands.command(aliases=["with"])
    async def withdraw(self, ctx, amount: str):
        """Take money out of your bank for purchases."""
        player = await players.find_one({"user_id": ctx.author.id})
        bank = player.get("bank", 0)
        
        if amount.lower() == "all": amount = bank
        else:
            if not amount.isdigit(): return await ctx.send("❌ Enter a valid amount.")
            amount = int(amount)
            
        if amount > bank: return await ctx.send("❌ Insufficient bank balance!")
        
        await players.update_one({"user_id": ctx.author.id}, {"$inc": {"money": amount, "bank": -amount}})
        await ctx.send(f"🏧 **Withdrawal Complete:** ${amount} added to your wallet.")

    @commands.command()
    async def loan(self, ctx, amount: int):
        """Borrow money. Limits and rates depend on your Credit Score."""
        player = await players.find_one({"user_id": ctx.author.id})
        if not player: return await ctx.send("❌ Use `!start` first!")
        
        credit = player.get("credit_score", 500)
        
        # Modern dynamic limits based on credit
        if credit < 300: max_loan = 0
        elif credit < 500: max_loan = 2000
        elif credit < 700: max_loan = 5000
        else: max_loan = 10000

        if max_loan == 0:
            return await ctx.send("❌ **Denied:** Your Credit Score is too low (< 300). Work on your reputation first!")
        
        if amount > max_loan:
            return await ctx.send(f"❌ **Denied:** Based on your Credit Score ({credit}), your max loan is **${max_loan}**.")
        
        if amount <= 0: return await ctx.send("❌ Invalid amount.")
        if player.get("debt", 0) > 0:
            return await ctx.send("❌ **Access Denied:** You still have an active debt to settle.")

        interest_rate = 1.05 if credit >= 500 else 1.10 # Better rate for better score
        total_debt = int(amount * interest_rate)
        
        await players.update_one({"user_id": ctx.author.id}, {"$inc": {"bank": amount, "debt": total_debt}})

        embed = discord.Embed(title="🏦 Bank of Arcadia: Loan Approved", color=discord.Color.gold())
        embed.add_field(name="Received", value=f"💰 ${amount}", inline=True)
        embed.add_field(name="Total Owed", value=f"📉 ${total_debt}", inline=True)
        embed.add_field(name="Credit Score", value=f"⭐ {credit}", inline=True)
        embed.set_footer(text="Keep cash in your bank for automatic daily repayments.")
        await ctx.send(embed=embed)

    @commands.command()
    async def bank(self, ctx):
        """View your personal banking and credit report."""
        player = await players.find_one({"user_id": ctx.author.id})
        if not player: return await ctx.send("❌ Use `!start` first!")
        
        embed = discord.Embed(title="🏦 Arcadia Banking Portal", color=discord.Color.dark_blue())
        embed.add_field(name="Balance", value=f"💵 ${player.get('bank', 0)} / ${player.get('bank_limit', 5000)}")
        embed.add_field(name="Current Debt", value=f"🚨 ${player.get('debt', 0)}")
        embed.add_field(name="Credit Score", value=f"⭐ {player.get('credit_score', 500)}")
        
        status = "Good Standing ✅" if player.get('debt', 0) == 0 else "Under Collection ⚠️"
        embed.add_field(name="Account Status", value=status, inline=False)
        
        embed.set_footer(text="Earn +1% interest daily on bank balances.")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
                    
