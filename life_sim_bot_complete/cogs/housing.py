import discord
from discord import app_commands
from discord.ext import commands
import json
from database.db import players

class HouseDropdown(discord.ui.Select):
    def __init__(self, housing_data, user_coins):
        self.housing_data = housing_data
        options = []
        for h in housing_data:
            label = h['name'].title()
            # Dynamic emoji based on affordability
            emoji = "🏠" if user_coins >= h['price'] else "🔒"
            options.append(discord.SelectOption(
                label=label,
                description=f"Price: ${h['price']} | Happiness: +{h.get('happiness', 0)}",
                value=h['name'],
                emoji=emoji
            ))
        super().__init__(placeholder="Select a property to purchase...", options=options)

    async def callback(self, interaction: discord.Interaction):
        # Prevent "Interaction Failed"
        await interaction.response.defer(ephemeral=True)
        
        house_name = self.values[0]
        house_data = next((h for h in self.housing_data if h["name"] == house_name), None)
        
        player = await players.find_one({"user_id": interaction.user.id})
        if not player:
            return await interaction.followup.send("❌ Use `/start` first.")

        current_cash = player.get("money", 0)
        if current_cash < house_data['price']:
            return await interaction.followup.send(f"❌ You need ${house_data['price']}!")

        # Database Update: Apply all stats
        new_balance = current_cash - house_data['price']
        await players.update_one(
            {"user_id": interaction.user.id},
            {
                "$set": {"house": house_name},
                "$inc": {
                    "money": -house_data['price'],
                    "stats.happiness": house_data.get("happiness", 0),
                    "stats.energy": house_data.get("energy", 0),
                    "stats.comfort": house_data.get("comfort", 0)
                }
            }
        )

        # Build the Visual Embed (Matching image_e48ab8.png)
        embed = discord.Embed(
            title="🎉 Property Purchased!",
            description=f"Welcome home! You successfully moved into the **{house_name.title()}**.\n\n*{house_data.get('description')}*",
            color=discord.Color.gold()
        )
        
        # Left Column: Stats
        boosts = (
            f"😊 **Happiness:** +{house_data.get('happiness')}\n"
            f"⚡ **Energy:** +{house_data.get('energy')}\n"
            f"🛋️ **Comfort:** +{house_data.get('comfort')}"
        )
        embed.add_field(name="📈 Lifestyle Boosts", value=boosts, inline=True)
        
        # Right Column: Balance
        embed.add_field(name="💰 Remaining Balance", value=f"`${new_balance}`", inline=True)
        
        # Discord CDN Image
        if house_data.get("image"):
            embed.set_image(url=house_data["image"])

        await interaction.edit_original_response(embed=embed, view=None)

class HouseView(discord.ui.View):
    def __init__(self, housing_data, user_coins):
        super().__init__(timeout=60)
        self.add_item(HouseDropdown(housing_data, user_coins))

class Housing(commands.GroupCog, name="house"):
    def __init__(self, bot):
        self.bot = bot

    def get_data(self):
        with open("assets/housing.json", "r") as f:
            return json.load(f)

    @app_commands.command(name="buy", description="Browse and purchase property")
    async def buy(self, interaction: discord.Interaction):
        player = await players.find_one({"user_id": interaction.user.id})
        if not player:
            return await interaction.response.send_message("❌ Use `/start` first!", ephemeral=True)

        data = self.get_data()
        view = HouseView(data, player.get("money", 0))
        
        embed = discord.Embed(
            title="🏠 Arcadia Real Estate",
            description="Select a property from the menu below to move in.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Housing(bot))