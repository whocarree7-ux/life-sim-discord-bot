import discord
from discord import app_commands
from discord.ext import commands
import json
from database.db import players

class HouseDropdown(discord.ui.Select):
    def __init__(self, housing_data, owned_houses, user_coins):
        self.housing_list = housing_data
        options = []
        for h in housing_data:
            label = h['name'].title()
            is_owned = h['name'] in owned_houses
            is_too_expensive = user_coins < h['price'] and not is_owned
            
            options.append(discord.SelectOption(
                label=label,
                description=f"Already Owned" if is_owned else f"Price: ${h['price']}",
                value=h['name'],
                emoji="🏠" if not is_too_expensive else "🔒"
            ))
        super().__init__(placeholder="Browse properties...", options=options)

    async def callback(self, interaction: discord.Interaction):
        # 1. Get the selected house data
        house_name = self.values[0]
        house_data = next((h for h in self.housing_list if h["name"] == house_name), None)
        
        # 2. Get fresh player data
        player = await players.find_one({"user_id": interaction.user.id})
        owned_houses = player.get("owned_houses", ["shelter"])
        user_coins = player.get("money", 0)

        # 3. Update the view's current selection
        self.view.current_selection = house_data
        
        # 4. Prepare Embed
        is_owned = house_name in owned_houses
        color = discord.Color.green() if is_owned else discord.Color.blue()
        
        embed = discord.Embed(title=f"🏠 Property: {house_name.title()}", color=color)
        embed.description = house_data.get("description", "A beautiful property in the heart of Arcadia.")
        
        if "image" in house_data: 
            embed.set_image(url=house_data["image"])
        
        embed.add_field(name="💰 Price", value=f"${house_data['price']}", inline=True)
        embed.add_field(name="📜 Status", value="Owned ✅" if is_owned else "Available 🛒", inline=True)

        # 5. Enable/Disable the Buy Button
        self.view.buy_btn.disabled = is_owned or user_coins < house_data['price']
        self.view.buy_btn.label = "Owned" if is_owned else "Buy Property"
        
        await interaction.response.edit_message(embed=embed, view=self.view)

class HouseView(discord.ui.View):
    def __init__(self, housing_list, owned_houses, user_coins):
        super().__init__(timeout=60)
        self.housing_list = housing_list
        self.current_selection = None
        
        # Add Dropdown
        self.add_item(HouseDropdown(housing_list, owned_houses, user_coins))
        
        # Add Buy Button
        self.buy_btn = discord.ui.Button(label="Select a House", style=discord.ButtonStyle.green, disabled=True)
        self.buy_btn.callback = self.buy_callback
        self.add_item(self.buy_btn)

    async def buy_callback(self, interaction: discord.Interaction):
        if not self.current_selection: return

        # Final check
        player = await players.find_one({"user_id": interaction.user.id})
        if player.get("money", 0) < self.current_selection['price']:
            return await interaction.response.send_message("❌ You ran out of money!", ephemeral=True)

        await players.update_one(
            {"user_id": interaction.user.id},
            {
                "$set": {"house": self.current_selection['name']},
                "$inc": {"money": -self.current_selection['price']},
                "$addToSet": {"owned_houses": self.current_selection['name']}
            }
        )

        await interaction.response.send_message(f"🎊 Congratulations! You are now the owner of a **{self.current_selection['name'].title()}**!", ephemeral=False)
        self.stop()

class Housing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.housing_data = self.load_housing()

    def load_housing(self):
        try:
            with open("assets/housing.json") as f:
                return json.load(f)
        except:
            return [{"name": "shelter", "price": 0, "description": "A basic place to stay."}]

    house_group = app_commands.Group(name="house", description="Property management")

    @house_group.command(name="buy")
    async def buy(self, interaction: discord.Interaction):
        player = await players.find_one({"user_id": interaction.user.id})
        if not player: return await interaction.response.send_message("❌ Use `/start` first.")

        view = HouseView(self.housing_data, player.get("owned_houses", ["shelter"]), player.get("money", 0))
        embed = discord.Embed(title="🏠 Arcadia Real Estate", description="Select a property from the menu to see its details.", color=discord.Color.blue())
        
        await interaction.response.send_message(embed=embed, view=view)

    @house_group.command(name="info")
    async def info(self, interaction: discord.Interaction):
        player = await players.find_one({"user_id": interaction.user.id})
        if not player: return await interaction.response.send_message("❌ Start your journey first!")
        
        current_house = player.get("house", "shelter")
        house_data = next((h for h in self.housing_data if h["name"] == current_house), self.housing_data[0])

        embed = discord.Embed(title=f"🏠 Your Home: {current_house.title()}", color=discord.Color.green())
        embed.description = house_data.get("description", "No description available.")
        
        embed.add_field(name="Market Value", value=f"${house_data.get('price', 0)}")
        embed.add_field(name="Ownership", value="Full Title Deed")
        
        if "image" in house_data: embed.set_image(url=house_data["image"])
        
        await interaction.response.send_message(embed=embed)

    @house_group.command(name="sell")
    async def sell(self, interaction: discord.Interaction):
        player = await players.find_one({"user_id": interaction.user.id})
        owned_houses = player.get("owned_houses", ["shelter"])
        sellable = [h for h in self.housing_data if h["name"] in owned_houses and h["name"] != "shelter"]

        if not sellable:
            return await interaction.response.send_message("❌ You have no properties to sell!", ephemeral=True)

        options = [discord.SelectOption(label=h['name'].title(), description=f"Sell for ${int(h['price']*0.5)}", value=h['name']) for h in sellable]
        select = discord.ui.Select(placeholder="Choose a house to sell...", options=options)

        async def sell_callback(si: discord.Interaction):
            target = select.values[0]
            house_item = next(h for h in self.housing_data if h["name"] == target)
            refund = int(house_item['price'] * 0.5)

            update = {"$pull": {"owned_houses": target}, "$inc": {"money": refund}}
            if player.get("house") == target: update["$set"] = {"house": "shelter"}

            await players.update_one({"user_id": interaction.user.id}, update)
            await si.response.edit_message(content=f"✅ Sold **{target.title()}** for **${refund}**!", view=None, embed=None)

        select.callback = sell_callback
        view = discord.ui.View(); view.add_item(select)
        await interaction.response.send_message("🏠 List a property for sale (50% value):", view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Housing(bot))
