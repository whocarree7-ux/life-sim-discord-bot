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
            
            # Show a lock if they don't own it and can't afford it
            emoji = "🏠"
            if not is_owned and user_coins < h['price']:
                emoji = "🔒"
            elif is_owned:
                emoji = "✅"

            options.append(discord.SelectOption(
                label=label,
                description=f"Owner" if is_owned else f"Price: ${h['price']}",
                value=h['name'],
                emoji=emoji
            ))
        super().__init__(placeholder="🏢 Browse Arcadia Real Estate...", options=options)

    async def callback(self, interaction: discord.Interaction):
        house_name = self.values[0]
        house_data = next((h for h in self.housing_list if h["name"] == house_name), None)
        
        # Fresh data fetch
        player = await players.find_one({"user_id": interaction.user.id})
        owned_houses = player.get("owned_houses", ["shelter"])
        current_house = player.get("house", "shelter")
        user_coins = player.get("money", 0)

        self.view.current_selection = house_data
        is_owned = house_name in owned_houses
        
        # Setup Embed
        color = discord.Color.gold() if is_owned else discord.Color.blue()
        embed = discord.Embed(title=f"🏠 Property: {house_name.title()}", color=color)
        embed.description = f"**Description:**\n{house_data.get('description', 'A property in Arcadia.')}"
        
        if "image" in house_data: 
            embed.set_image(url=house_data["image"])
        
        # Display all stats from housing.json
        embed.add_field(name="💰 Price", value=f"${house_data['price']}", inline=True)
        embed.add_field(name="😊 Happiness", value=f"+{house_data.get('happiness', 0)}", inline=True)
        embed.add_field(name="⚡ Energy", value=f"+{house_data.get('energy', 0)}", inline=True)
        embed.add_field(name="🛋️ Comfort", value=f"{house_data.get('comfort', 0)}", inline=True)
        embed.add_field(name="📜 Ownership", value="Verified ✅" if is_owned else "Available 🛒", inline=True)

        # Logic for Button State
        if is_owned:
            if house_name == current_house:
                self.view.action_btn.label = "Current Home"
                self.view.action_btn.style = discord.ButtonStyle.grey
                self.view.action_btn.disabled = True
            else:
                self.view.action_btn.label = "Move In"
                self.view.action_btn.style = discord.ButtonStyle.blurple
                self.view.action_btn.disabled = False
        else:
            if user_coins >= house_data['price']:
                self.view.action_btn.label = "Buy Property"
                self.view.action_btn.style = discord.ButtonStyle.green
                self.view.action_btn.disabled = False
            else:
                self.view.action_btn.label = "Too Expensive"
                self.view.action_btn.style = discord.ButtonStyle.red
                self.view.action_btn.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self.view)

class HouseView(discord.ui.View):
    def __init__(self, housing_list, owned_houses, user_coins):
        super().__init__(timeout=60)
        self.housing_list = housing_list
        self.current_selection = None
        
        self.add_item(HouseDropdown(housing_list, owned_houses, user_coins))
        
        # Single action button that changes based on selection (Buy or Move In)
        self.action_btn = discord.ui.Button(label="Select a Property", style=discord.ButtonStyle.grey, disabled=True)
        self.action_btn.callback = self.action_callback
        self.add_item(self.action_btn)

    async def action_callback(self, interaction: discord.Interaction):
        if not self.current_selection: return
        
        player = await players.find_one({"user_id": interaction.user.id})
        owned_houses = player.get("owned_houses", ["shelter"])
        house_name = self.current_selection['name']

        # Scenario A: User already owns it -> Move In
        if house_name in owned_houses:
            await players.update_one({"user_id": interaction.user.id}, {"$set": {"house": house_name}})
            await interaction.response.send_message(f"🚚 You have moved into your **{house_name.title()}**!", ephemeral=True)
        
        # Scenario B: User is buying it
        else:
            if player.get("money", 0) < self.current_selection['price']:
                return await interaction.response.send_message("❌ Transaction failed: Insufficient funds.", ephemeral=True)

            await players.update_one(
                {"user_id": interaction.user.id},
                {
                    "$set": {"house": house_name},
                    "$inc": {"money": -self.current_selection['price']},
                    "$addToSet": {"owned_houses": house_name}
                }
            )
            await interaction.response.send_message(f"🎊 Purchase Successful! Enjoy your new **{house_name.title()}**!", ephemeral=False)
        
        self.stop()

class Housing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.housing_data = self.load_housing()

    def load_housing(self):
        try:
            with open("assets/housing.json") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading housing.json: {e}")
            return [{"name": "shelter", "price": 0, "description": "Basic shelter."}]

    house_group = app_commands.Group(name="house", description="Arcadia Real Estate Management")

    @house_group.command(name="buy", description="Browse and purchase new properties")
    async def buy(self, interaction: discord.Interaction):
        player = await players.find_one({"user_id": interaction.user.id})
        if not player: return await interaction.response.send_message("❌ Use `/start` first.")

        view = HouseView(self.housing_data, player.get("owned_houses", ["shelter"]), player.get("money", 0))
        embed = discord.Embed(
            title="🏙️ Arcadia Real Estate Market", 
            description="Use the menu below to view luxury apartments and cozy homes.", 
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=view)

    @house_group.command(name="info", description="View details of your current home")
    async def info(self, interaction: discord.Interaction):
        player = await players.find_one({"user_id": interaction.user.id})
        if not player: return await interaction.response.send_message("❌ Start your journey first!")
        
        current_house = player.get("house", "shelter")
        house_data = next((h for h in self.housing_data if h["name"] == current_house), self.housing_data[0])

        embed = discord.Embed(title=f"🏠 Current Home: {current_house.title()}", color=discord.Color.green())
        embed.description = f"*{house_data.get('description', 'No description available.')}*"
        
        embed.add_field(name="😊 Happiness", value=f"+{house_data.get('happiness', 0)}", inline=True)
        embed.add_field(name="⚡ Energy Boost", value=f"+{house_data.get('energy', 0)}", inline=True)
        embed.add_field(name="🛋️ Comfort", value=f"{house_data.get('comfort', 0)}", inline=True)
        embed.add_field(name="💰 Market Value", value=f"${house_data.get('price', 0)}", inline=True)
        
        if "image" in house_data: embed.set_image(url=house_data["image"])
        
        await interaction.response.send_message(embed=embed)

    @house_group.command(name="sell", description="Sell a property for 50% of its value")
    async def sell(self, interaction: discord.Interaction):
        player = await players.find_one({"user_id": interaction.user.id})
        owned_houses = player.get("owned_houses", ["shelter"])
        sellable = [h for h in self.housing_data if h["name"] in owned_houses and h["name"] != "shelter"]

        if not sellable:
            return await interaction.response.send_message("❌ You have no properties to sell!", ephemeral=True)

        options = [
            discord.SelectOption(
                label=h['name'].title(), 
                description=f"Refund: ${int(h['price']*0.5)}", 
                value=h['name']
            ) for h in sellable
        ]
        
        select = discord.ui.Select(placeholder="Select property to list...", options=options)

        async def sell_callback(si: discord.Interaction):
            target = select.values[0]
            house_item = next(h for h in self.housing_data if h["name"] == target)
            refund = int(house_item['price'] * 0.5)

            update = {"$pull": {"owned_houses": target}, "$inc": {"money": refund}}
            if player.get("house") == target: 
                update["$set"] = {"house": "shelter"}

            await players.update_one({"user_id": interaction.user.id}, update)
            await si.response.edit_message(content=f"✅ Property Sold! You received **${refund}**.", view=None, embed=None)

        select.callback = sell_callback
        view = discord.ui.View()
        view.add_item(select)
        await interaction.response.send_message("💼 **Agent:** Select a property to put on the market:", view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Housing(bot))
