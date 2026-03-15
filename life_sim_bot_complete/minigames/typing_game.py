import discord
import asyncio
import random

class TypingGame:  # <--- THIS NAME MUST BE EXACTLY 'TypingGame'
    async def start(self, ctx):
        sentences = ["The quick brown fox", "Arcadia is the best city", "Omnix Life Bot"]
        target = random.choice(sentences)
        
        await ctx.send(f"⌨️ **Type this exactly:** `{target}`")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await ctx.bot.wait_for("message", check=check, timeout=15.0)
            if msg.content == target:
                return True
            else:
                await ctx.send("❌ Incorrect typing!")
                return False
        except asyncio.TimeoutError:
            await ctx.send("⏰ Too slow!")
            return False
