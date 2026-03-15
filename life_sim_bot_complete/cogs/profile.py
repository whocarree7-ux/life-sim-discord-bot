import discord
from discord.ext import commands
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

    @commands.command()
    async def start(self, ctx):
        existing = await players.find_one({"user_id": ctx.author.id})
        if existing:
            return await ctx.send("❌ You already have a profile! Use `!profile` to see it.")

        background = random.choice(self.backgrounds)
        player = default_player(ctx.author.id, background)

        await players.insert_one(player)

        embed = discord.Embed(
            title="✨ New Life Started!",
            description=f"Welcome to Arcadia, **{ctx.author.name}**!\nYour background is: **{background['name']}**.",
            color=discord.Color.green()
        )
        embed.add_field(name="💰 Starting Cash", value=f"${background['money']}")
        await ctx.send(embed=embed)

    @commands.command()
    async def profile(self, ctx):
        player = await players.find_one({"user_id": ctx.author.id})

        if not player:
            return await ctx.send("❌ You haven't started your life yet. Type `!start`!")

        # Pull stats safely with .get() to avoid KeyErrors
        money = player.get("money", 0)
        bank = player.get("bank", 0)
        bank_limit = player.get("bank_limit", 5000)
        job = player.get("job", "Unemployed").replace("_", " ").title()
        house = player.get("house", "Shelter").title()
        stats = player.get("stats", {})

        embed = discord.Embed(
            title=f"👤 {ctx.author.name}'s Identity Card",
            color=discord.Color.blue()
        )

        # Category 1: Finances
        embed.add_field(
            name="💰 Finances", 
            value=f"**Cash:** `${money}`\n**Bank:** `${bank}` / `${bank_limit}`", 
            inline=True
        )

        # Category 2: Career & Living
        embed.add_field(
            name="🏠 Lifestyle", 
            value=f"**Job:** {job}\n**House:** {house}", 
            inline=True
        )

        # Category 3: Reputation (Full Row)
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

        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Profile(bot))
