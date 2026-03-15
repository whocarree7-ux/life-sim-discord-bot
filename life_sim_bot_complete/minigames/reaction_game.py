import discord
import asyncio
import random

class ReactionGame:
    async def start(self, ctx):
        emoji = "🎯"
        msg = await ctx.send("Get ready...")
        await asyncio.sleep(random.randint(2, 5))
        await msg.edit(content=f"REACT NOW! {emoji}")
        await msg.add_reaction(emoji)

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == emoji and reaction.message.id == msg.id

        try:
            # User has 2 seconds to react
            await ctx.bot.wait_for("reaction_add", timeout=5.0, check=check)
            return True
        except asyncio.TimeoutError:
            return False
