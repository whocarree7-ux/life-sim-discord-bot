import discord
from discord.ext import commands
from discord import app_commands
import random
import json
from database.db import players
from database.models import default_player

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            with open("assets/backgrounds.json") as f:
                self.backgrounds = json.load(f)
        except:
            # Fallback if the JSON is missing
            self.backgrounds = [{"name": "Average Citizen", "money": 500}]

    @app_commands.command(name="start", description="Begin your new life in Arcadia")
    async def start(self, interaction: discord.Interaction):
        existing = await players.find_one({"user_id": interaction.user.id})
        
        if existing:
            return await interaction.response.send_message("❌ You already have a profile! Use `/profile` to see it.", ephemeral=True)

        # Select a random starting background
        background = random.choice(self.backgrounds)
        player = default_player(interaction.user.id, background)

        await players.insert_one(player)

        embed = discord.Embed(
            title="✨ New Life Started!",
            description=f"Welcome to Arcadia, **{interaction.user.name}**!\nYour background is: **{background['name']}**.",
            color=discord.Color.green()
        )
        embed.add_field(name="💰 Starting Cash", value=f"${background['money']}")
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profile", description="View your identity card, stats, and lifestyle")
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        # Allow looking at others' profiles, default to self
        target = member or interaction.user
        player = await players.find_one({"user_id": target.id})

        if not player:
            message = "❌ You haven't started your life yet. Type `/start`!" if target == interaction.user else f"❌ {target.name} doesn't have a profile yet."
            return await interaction.response.send_message(message, ephemeral=True)

        # Pull data safely
        money = player.get("money", 0)
        bank = player.get("bank", 0)
        bank_limit = player.get("bank_limit", 5000)
        job = player.get("job", "Unemployed").replace("_", " ").title()
        house = player.get("house", "Shelter").title()
        stats = player.get("stats", {})

        embed = discord.Embed(
            title=f"👤 {target.name}'s Identity Card",
            color=discord.Color.blue()
        )

        # Category 1: Finances
        embed.add_field(
            name="💰 Finances", 
            value=f"**Cash:** `${money}`\n**Bank:** `${bank}` / `${bank_limit}`", 
            inline=True
        )

        # Category 2: Lifestyle
        embed.add_field(
            name="🏠 Lifestyle", 
            value=f"**Job:** {job}\n**House:** {house}", 
            inline=True
        )

        # Category 3: Reputation
        embed.add_field(
            name="⭐ Reputation", 
            value=f"`{stats.get('reputation', 0)}` points", 
            inline=False
        )

        # Category 4: Physical & Mental Stats
        attributes = (
            f"🧠 **INT:** {stats.get('intelligence', 0)} | 💪 **STR:** {stats.get('strength', 0)} | 🗣️ **CHA:** {stats.get('charisma', 0)}\n"
            f"❤️ **HP:** {stats.get('health', 0)}% | ⚡ **NRG:** {stats.get('energy', 0)}%"
        )
        embed.add_field(name="📊 Attributes", value=attributes, inline=False)

        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="Arcadia Identity Management")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Profile(bot))