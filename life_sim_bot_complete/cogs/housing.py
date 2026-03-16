import discord
from discord import app_commands
from discord.ext import commands
import json
from database.db import players

class HouseDropdown(discord.ui.Select):
    def __init__(self, housing_data, user_coins):
        options = []
        for h in housing_data:
            label = h['name'].title()
            is_too_expensive = user_coins < h['price']
            
            options.append(discord.SelectOption(
                label=label,
                description=f"Price: ${h['price']}",
                value=h['name'],
                emoji="🏠" if not is_too_expensive else "🔒"
            ))
        super().__init__(placeholder="Select a property to buy...", options=options)

    async def callback(self, interaction: discord.Interaction):
        house_name = self.values[0]
        house_data = next((h for h in self.view.housing_list if h["name"] == house_name), None)
        
        player = await players.find_one({"user_id": interaction.user.id})
        if not player:
            return await interaction.response.send_message("❌ Use `!start` first.", ephemeral=True)

        user_coins = player.get("money", 0)

        if user_coins < house_data['price']:
            return await interaction.response.send_message(f"❌ You need ${house_data['price']} to buy this!", ephemeral=True)

        # Update Database
        await players.update_one(
            {"user_id": interaction.user.id},
            {
                "$set": {"house": house_name},
                "$inc": {"money": -house_data['price']}
            }
        )

        # Success Embed with Description
        embed = discord.Embed(
            title="🏠 Property Purchased!",
            description=f"Congratulations! You are now the proud owner of a **{house_name.title()}**.",
            color=discord.Color.gold()
        )
        if "image" in house_data:
            embed.set_thumbnail(url=house_data["image"])
            
        embed.add_field(name="Purchase Price", value=f"${house_data['price']}")
        embed.add_field(name="New Address", value="Arcadia Heights")
        embed.set_footer(text="Arcadia Real Estate")

        await interaction.response.edit_message(embed=embed, view=None)

class HouseView(discord.ui.View):
    def __init__(self, housing_list, user_coins):
        super().__init__(timeout=60)
        self.housing_list = housing_list
        self.add_item(HouseDropdown(housing_list, user_coins))

class Housing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            with open("assets/housing.json") as f:
                self.housing_data = json.load(f)
        except Exception as e:
            print(f"Housing JSON Error: {e}")
            self.housing_data = [{"name": "shelter", "price": 0}]

    house_group = app_commands.Group(name="house", description="Real Estate commands")

    @house_group.command(name="buy", description="Browse and buy properties")
    async def buy(self, interaction: discord.Interaction):
        player = await players.find_one({"user_id": interaction.user.id})
        if not player:
            return await interaction.response.send_message("❌ Use `!start` first.", ephemeral=True)

        user_coins = player.get("money", 0)
        view = HouseView(self.housing_data, user_coins)
        
        embed = discord.Embed(
            title="🏠 Arcadia Real Estate",
            description="Looking for a new place to stay? Select a property from the menu below.",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Your Balance: ${user_coins}")
        
        await interaction.response.send_message(embed=embed, view=view)

    @house_group.command(name="info", description="View your current house details")
    async def info(self, interaction: discord.Interaction):
        player = await players.find_one({"user_id": interaction.user.id})
        if not player:
            return await interaction.response.send_message("❌ Use `!start` first.", ephemeral=True)

        current_house = player.get("house", "shelter")
        house_data = next((h for h in self.housing_data if h["name"] == current_house), self.housing_data[0])

        embed = discord.Embed(
            title="🏠 Your Residence",
            description=f"You are currently living in a **{current_house.title()}**.",
            color=discord.Color.green()
        )
        
        if house_data and "image" in house_data:
            embed.set_image(url=house_data["image"])

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Housing(bot))
