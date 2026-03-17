import discord
import asyncio
import random

class MemoryGame:
    def __init__(self):
        self.emojis = ["🍎", "💎", "🛡️", "🚀", "🎮", "🐱", "🌈", "🍕"]

    async def start(self, ctx):
        # 1. Pick a sequence of 4 random emojis
        sequence = random.sample(self.emojis, 4)
        display_seq = " ".join(sequence)
        answer_seq = "".join(sequence)

        # 2. Show the sequence to the user
        game_msg = await ctx.send(
            f"🧠 **Memory Task:** Remember this sequence!\n\n"
            f"> **{display_seq}**\n\n"
            f"*It will disappear in 5 seconds...*"
        )

        # 3. Wait 5 seconds then hide it
        await asyncio.sleep(5)
        await game_msg.edit(content="🧠 **Memory Task:** What was the sequence? (Type the emojis without spaces)")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            # 4. Wait for the user's answer
            user_msg = await ctx.bot.wait_for("message", check=check, timeout=20.0)
            
            # Clean the user input (remove spaces if they added them)
            user_answer = user_msg.content.replace(" ", "")

            if user_answer == answer_seq:
                return True
            else:
                await ctx.send(f"❌ **Wrong!** The correct order was: {display_seq}")
                return False

        except asyncio.TimeoutError:
            await ctx.send(f"⏰ **Time's up!** You took too long to answer.")
            return False
