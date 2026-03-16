import discord
from discord.ext import commands
from discord import app_commands

houses = {
    "hut": 500,
    "cabin": 1500,
    "villa": 5000
}

player_data = {}

class Island(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    island = app_commands.Group(name="island", description="Island management commands")

    @island.command(name="profile", description="View your island profile")
    async def profile(self, interaction: discord.Interaction):

        user = interaction.user.id
        data = player_data.get(user, {"house": "None", "coins": 1000})

        embed = discord.Embed(
            title="🏝 Island Profile",
            color=discord.Color.gold()
        )

        embed.add_field(name="House", value=data["house"])
        embed.add_field(name="Coins", value=data["coins"])

        await interaction.response.send_message(embed=embed)

    @island.command(name="buyhouse", description="Buy a house")
    async def buyhouse(self, interaction: discord.Interaction, house: str):

        house = house.lower()
        user = interaction.user.id

        if house not in houses:
            return await interaction.response.send_message(
                "Available houses: hut, cabin, villa"
            )

        data = player_data.setdefault(user, {"house": "None", "coins": 1000})

        price = houses[house]

        if data["coins"] < price:
            return await interaction.response.send_message(
                f"You need {price} coins to buy a {house}"
            )

        data["coins"] -= price
        data["house"] = house

        await interaction.response.send_message(
            f"🏠 You bought a **{house}** for {price} coins!"
        )

    @island.command(name="house", description="Check your house")
    async def house(self, interaction: discord.Interaction):

        user = interaction.user.id
        data = player_data.get(user, {"house": "None", "coins": 1000})

        await interaction.response.send_message(
            f"🏠 Your house: **{data['house']}**"
        )


async def setup(bot):
    await bot.add_cog(Island(bot))