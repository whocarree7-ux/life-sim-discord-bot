import discord
from discord import app_commands
from discord.ext import commands
import json
from database.db import players

class HouseDropdown(discord.ui.Select):
    def __init__(self, housing_data, owned_houses, user_coins):
        options = []
        for h in housing_data:
            label = h['name'].title()
            # Check if player already owns this house
            is_owned = h['name'] in owned_houses
            is_too_expensive = user_coins < h['price'] and not is_owned
            
            options.append(discord.SelectOption(
                label=label,
                description="Already Owned ✅" if is_owned else f"Price: ${h['price']}",
                value=h['name'],
                emoji="🏠" if not is_too_expensive else "🔒"
            ))
        super().__init__(placeholder="Choose a property...", options=options)

    async def callback(self, interaction: discord.Interaction):
        house_name = self.values[0]
        house_data = next((h for h in self.view.housing_list if h["name"] == house_name), None)
        
        player = await players.find_one({"user_id": interaction.user.id})
        owned_houses = player.get("owned_houses", ["shelter"])
        current_house = player.get("house", "shelter")

        if house_name == current_house:
            return await interaction.response.send_message(f"🏠 You are already in your **{house_name.title()}**!", ephemeral=True)

        # Free switch if owned
        if house_name in owned_houses:
            await players.update_one({"user_id": interaction.user.id}, {"$set": {"house": house_name}})
            return await interaction.response.send_message(f"🚚 You moved back to your **{house_name.title()}**!", ephemeral=True)

        # Purchase logic
        user_coins = player.get("money", 0)
        if user_coins < house_data['price']:
            return await interaction.response.send_message(f"❌ You can't afford a {house_name.title()}!", ephemeral=True)

        await players.update_one(
            {"user_id": interaction.user.id},
            {
                "$set": {"house": house_name},
                "$inc": {"money": -house_data['price']},
                "$addToSet": {"owned_houses": house_name}
            }
        )

        embed = discord.Embed(title="🏠 New Home Unlocked!", color=discord.Color.gold())
        if "image" in house_data: embed.set_thumbnail(url=house_data["image"])
        embed.add_field(name="Property", value=house_name.title())
        embed.add_field(name="Price Paid", value=f"${house_data['price']}")

        await interaction.response.edit_message(embed=embed, view=None)

class HouseView(discord.ui.View):
    def __init__(self, housing_list, owned_houses, user_coins):
        super().__init__(timeout=60)
        self.housing_list = housing_list
        # Added the dropdown to the view
        self.add_item(HouseDropdown(housing_list, owned_houses, user_coins))

class Housing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            with open("assets/housing.json") as f:
                self.housing_data = json.load(f)
        except:
            self.housing_data = [{"name": "shelter", "price": 0}]

    house_group = app_commands.Group(name="house", description="Property management")

    @house_group.command(name="buy")
    async def buy(self, interaction: discord.Interaction):
        player = await players.find_one({"user_id": interaction.user.id})
        if not player: return await interaction.response.send_message("❌ Use `!start` first.")

        user_coins = player.get("money", 0)
        owned = player.get("owned_houses", ["shelter"])
        
        # Pass data to the view
        view = HouseView(self.housing_data, owned, user_coins)
        
        embed = discord.Embed(title="🏠 Real Estate Market", description="Upgrade your lifestyle!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, view=view)

    @house_group.command(name="info")
    async def info(self, interaction: discord.Interaction):
        player = await players.find_one({"user_id": interaction.user.id})
        current_house = player.get("house", "shelter")
        house_data = next((h for h in self.housing_data if h["name"] == current_house), self.housing_data[0])

        embed = discord.Embed(title=f"🏠 Current Home: {current_house.title()}", color=discord.Color.green())
        if "image" in house_data: embed.set_image(url=house_data["image"])
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Housing(bot))
