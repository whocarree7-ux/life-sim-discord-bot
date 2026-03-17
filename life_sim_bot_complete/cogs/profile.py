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
            self.backgrounds = [{"name": "Average Citizen", "money": 500}]

    @app_commands.command(name="start", description="Begin your new life in Arcadia")
    async def start(self, interaction: discord.Interaction):
        existing = await players.find_one({"user_id": interaction.user.id})
        if existing:
            return await interaction.response.send_message("❌ You already have a profile!", ephemeral=True)

        background = random.choice(self.backgrounds)
        player = default_player(interaction.user.id, background)
        await players.insert_one(player)

        embed = discord.Embed(
            title="✨ New Life Started!",
            description=f"Welcome to Arcadia, **{interaction.user.name}**!\nYour background is: **{background['name']}**.",
            color=discord.Color.green()
        )
        embed.add_field(name="💰 Starting Cash", value=f" ${background['money']}")
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    # --- NEW DAILY COMMAND (Added without changing start/profile) ---
    @app_commands.command(name="daily", description="Claim your daily money and energy rewards")
    @app_commands.checks.cooldown(1, 86400, key=lambda i: i.user.id) 
    async def daily(self, interaction: discord.Interaction):
        player = await players.find_one({"user_id": interaction.user.id})
        if not player:
            return await interaction.response.send_message("❌ Use `/start` first!", ephemeral=True)

        money_gain = 250
        energy_gain = 30

        await players.update_one(
            {"user_id": interaction.user.id},
            {"$inc": {"money": money_gain, "stats.energy": energy_gain}}
        )

        embed = discord.Embed(
            title="🌞 Daily Reward",
            description="You claimed your daily care package!",
            color=discord.Color.gold()
        )
        embed.add_field(name="💰 Cash", value=f"+${money_gain}")
        embed.add_field(name="⚡ Energy", value=f"+{energy_gain}%")
        await interaction.response.send_message(embed=embed)

    @daily.error
    async def daily_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            seconds = int(error.retry_after)
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return await interaction.response.send_message(
                f"⏳ Try again in **{hours}h {minutes}m {seconds}s**.", ephemeral=True
            )

    @app_commands.command(name="profile", description="View your identity card")
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        player = await players.find_one({"user_id": target.id})

        if not player:
            message = "❌ No profile found."
            return await interaction.response.send_message(message, ephemeral=True)

        money = player.get("money", 0)
        bank = player.get("bank", 0)
        stats = player.get("stats", {})

        embed = discord.Embed(title=f"👤 {target.name}'s Profile", color=discord.Color.blue())
        embed.add_field(name="💰 Cash", value=f"${money}", inline=True)
        embed.add_field(name="⚡ Energy", value=f"{stats.get('energy', 0)}%", inline=True)
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Profile(bot))