import discord
from discord.ext import commands, tasks
from database.db import players
from systems.investment_system import market

class Investments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.market_loop.start()

    def cog_unload(self):
        self.market_loop.cancel()

    @tasks.loop(hours=0.5)
    async def market_loop(self):
        """Update market prices every hour."""
        market.update_market()
        print("📈 Market prices updated.")

    @commands.command(aliases=["market", "stocks"])
    async def prices(self, ctx):
        """Check current Gold and Crypto prices."""
        prices = market.prices
        embed = discord.Embed(title="📊 Arcadia Exchange Market", color=discord.Color.purple())
        embed.add_field(name="🟡 Gold", value=f"${prices['gold']} / oz", inline=True)
        embed.add_field(name="🌌 Crypto (ARC)", value=f"${prices['crypto']} / coin", inline=True)
        embed.set_footer(text="Prices update every hour!")
        await ctx.send(embed=embed)

    @commands.command()
    async def buy(self, ctx, asset: str, amount: int):
        """Buy Gold or Crypto. Usage: !buy gold 2"""
        asset = asset.lower()
        if asset not in ["gold", "crypto"]:
            return await ctx.send("❌ Choose either `gold` or `crypto`.")
        
        player = await players.find_one({"user_id": ctx.author.id})
        cost = market.prices[asset] * amount
        
        if player.get("money", 0) < cost:
            return await ctx.send(f"❌ You need **${cost}** in your wallet to buy this!")

        # Update database: Remove money, Add asset to 'investments' dictionary
        await players.update_one(
            {"user_id": ctx.author.id},
            {
                "$inc": {
                    "money": -cost,
                    f"investments.{asset}": amount
                }
            }
        )
        await ctx.send(f"✅ Bought **{amount}** {asset} for **${cost}**.")

    @commands.command()
    async def sell(self, ctx, asset: str, amount: int):
        """Sell your assets at current market price."""
        asset = asset.lower()
        player = await players.find_one({"user_id": ctx.author.id})
        
        owned = player.get("investments", {}).get(asset, 0)
        if owned < amount:
            return await ctx.send(f"❌ You only have **{owned}** {asset}!")

        gain = market.prices[asset] * amount
        await players.update_one(
            {"user_id": ctx.author.id},
            {
                "$inc": {
                    "money": gain,
                    f"investments.{asset}": -amount
                }
            }
        )
        await ctx.send(f"📉 Sold **{amount}** {asset} for **${gain}**. Money added to wallet!")

async def setup(bot):
    await bot.add_cog(Investments(bot))
      
