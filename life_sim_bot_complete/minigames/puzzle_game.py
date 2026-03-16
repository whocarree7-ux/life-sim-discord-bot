import discord
import random
import asyncio

class PuzzleGame:  # <--- MUST be spelled exactly like this
    def __init__(self):
        pass

    async def start(self, ctx):
        # A simple math puzzle for work
        num1 = random.randint(1, 20)
        num2 = random.randint(1, 20)
        answer = num1 + num2
        
        await ctx.send(f"🧩 **Work Puzzle:** What is `{num1} + {num2}`?")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

        try:
            msg = await ctx.bot.wait_for("message", check=check, timeout=15.0)
            if int(msg.content) == answer:
                return True
            else:
                await ctx.send(f"❌ Wrong! The answer was {answer}.")
                return False
        except asyncio.TimeoutError:
            await ctx.send("⏰ Time ran out!")
            return False
