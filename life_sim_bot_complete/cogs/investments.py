import discord
from discord.ext import commands, tasks
from discord import app_commands
from database.db import players
from systems.investment_system import market


class Investments(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.market_loop.start()

    def cog_unload(self):
        self.market_loop.cancel()

    @tasks.loop(hours=1)
    async def market_loop(self):
        market.update_market()
        print("📈 Market prices updated")

    # -------------------
    # /market
    # -------------------
    @app_commands.command(name="market", description="Check Gold and Crypto prices")
    async def market_cmd(self, interaction: discord.Interaction):

        prices = market.markets

        embed = discord.Embed(
            title="📊 Omnix Island Market",
            color=discord.Color.green()
        )

        embed.add_field(
            name="🟡 Gold",
            value=f"${prices['gold']}",
            inline=True
        )

        embed.add_field(
            name="🌌 Crypto",
            value=f"${prices['crypto']}",
            inline=True
        )

        embed.set_footer(text="Prices update every hour")

        await interaction.response.send_message(embed=embed)

    # -------------------
    # /buy
    # -------------------
    @app_commands.command(name="buy", description="Buy Gold or Crypto")
    async def buy(self, interaction: discord.Interaction, asset: str, amount: int):

        asset = asset.lower()

        if asset not in ["gold", "crypto"]:
            return await interaction.response.send_message(
                "❌ Choose `gold` or `crypto`"
            )

        player = await players.find_one({"user_id": interaction.user.id})

        if not player:
            return await interaction.response.send_message(
                "Use `/start` first to create your profile"
            )

        cost = market.markets[asset] * amount

        if player.get("money", 0) < cost:
            return await interaction.response.send_message(
                f"❌ You need **${cost}**"
            )

        await players.update_one(
            {"user_id": interaction.user.id},
            {
                "$inc": {
                    "money": -cost,
                    f"investments.{asset}": amount
                }
            }
        )

        await interaction.response.send_message(
            f"✅ Bought **{amount} {asset}** for **${cost}**"
        )

    # -------------------
    # /sell
    # -------------------
    @app_commands.command(name="sell", description="Sell your assets")
    async def sell(self, interaction: discord.Interaction, asset: str, amount: int):

        asset = asset.lower()

        player = await players.find_one({"user_id": interaction.user.id})

        if not player:
            return await interaction.response.send_message(
                "Use `/start` first"
            )

        owned = player.get("investments", {}).get(asset, 0)

        if owned < amount:
            return await interaction.response.send_message(
                f"❌ You only own **{owned} {asset}**"
            )

        gain = market.markets[asset] * amount

        await players.update_one(
            {"user_id": interaction.user.id},
            {
                "$inc": {
                    "money": gain,
                    f"investments.{asset}": -amount
                }
            }
        )

        await interaction.response.send_message(
            f"📉 Sold **{amount} {asset}** for **${gain}**"
        )


async def setup(bot):
    await bot.add_cog(Investments(bot))