import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import time
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

    @commands.hybrid_command(name="start", description="Begin your new life in Arcadia")
    async def start(self, ctx: commands.Context):
        existing = await players.find_one({"user_id": ctx.author.id})
        
        if existing:
            return await ctx.send("❌ You already have a profile! Use `/profile` to see it.", ephemeral=True)

        background = random.choice(self.backgrounds)
        player = default_player(ctx.author.id, background)
        await players.insert_one(player)

        embed = discord.Embed(
            title="✨ New Life Started!",
            description=f"Welcome to Arcadia, **{ctx.author.name}**!\nYour background is: **{background['name']}**.",
            color=discord.Color.green()
        )
        embed.add_field(name="💰 Starting Cash", value=f"${background['money']}")
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="profile", description="View your identity card, stats, and lifestyle")
    @app_commands.describe(member="The user whose profile you want to view")
    async def profile(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        player = await players.find_one({"user_id": target.id})

        if not player:
            message = "❌ You haven't started your life yet. Type `/start`!" if target == ctx.author else f"❌ {target.name} doesn't have a profile yet."
            return await ctx.send(message, ephemeral=True)

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

        embed.add_field(name="💰 Finances", value=f"**Cash:** `${money}`\n**Bank:** `${bank}` / `${bank_limit}`", inline=True)
        embed.add_field(name="🏠 Lifestyle", value=f"**Job:** {job}\n**House:** {house}", inline=True)
        embed.add_field(name="⭐ Reputation", value=f"`{stats.get('reputation', 0)}` points", inline=False)

        attributes = (
            f"🧠 **INT:** {stats.get('intelligence', 0)} | 💪 **STR:** {stats.get('strength', 0)} | 🗣️ **CHA:** {stats.get('charisma', 0)}\n"
            f"❤️ **HP:** {stats.get('health', 0)}% | ⚡ **NRG:** {stats.get('energy', 0)}%"
        )
        embed.add_field(name="📊 Attributes", value=attributes, inline=False)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="Arcadia Identity Management")

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="daily", description="Claim your daily Arcadia allowance")
    async def daily(self, ctx: commands.Context):
        player = await players.find_one({"user_id": ctx.author.id})

        if not player:
            return await ctx.send("❌ You haven't started your life yet! Use `/start` first.", ephemeral=True)

        last_daily = player.get("last_daily", 0)
        current_time = int(time.time())
        cooldown = 86400 

        if current_time - last_daily < cooldown:
            remaining = cooldown - (current_time - last_daily)
            hours, remainder = divmod(remaining, 3600)
            minutes, _ = divmod(remainder, 60)
            return await ctx.send(f"⏳ You've already claimed your daily! Come back in **{hours}h {minutes}m**.", ephemeral=True)

        reward = random.randint(500, 1500)
        
        await players.update_one(
            {"user_id": ctx.author.id},
            {"$inc": {"money": reward}, "$set": {"last_daily": current_time}}
        )

        embed = discord.Embed(
            title="🎁 Daily Allowance",
            description=f"You received your daily stipend of **${reward}**!",
            color=discord.Color.gold()
        )
        embed.set_footer(text="See you tomorrow!")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Profile(bot))