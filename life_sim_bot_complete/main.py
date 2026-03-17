import discord
from discord.ext import commands
from config import TOKEN
from database.db import init_db
import os
import asyncio

# IMPORTANT: Hybrid commands work best with All Intents 
# to ensure members/roles are found for commands like !pay
intents = discord.Intents.all() 

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await init_db()
    print(f"✅ Logged in as {bot.user}")
    print("💡 Tip: Use !sync to refresh slash commands if they don't show up.")

# -----------------------------
# MANUAL SYNC COMMAND
# -----------------------------
@bot.command()
@commands.is_owner() # Only you can run this
async def sync(ctx):
    try:
        # This sends your commands to Discord's servers
        synced = await bot.tree.sync()
        await ctx.send(f"🔄 Successfully synced {len(synced)} slash commands!")
    except Exception as e:
        await ctx.send(f"❌ Sync failed: {e}")

async def load_cogs():
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{file[:-3]}")
                print(f"📂 Loaded Cog: {file}")
            except Exception as e:
                print(f"⚠️ Failed to load {file}: {e}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
