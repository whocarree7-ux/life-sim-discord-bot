import discord
from discord.ext import commands
import random
import json
from database.db import players

# Import your mini-games
from minigames.reaction_game import ReactionGame
from minigames.typing_game import TypingGame

class Jobs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            with open("assets/jobs.json") as f:
                self.jobs = json.load(f)
        except:
            self.jobs = [{"name": "unemployed", "salary": 20, "req_rep": 0}]

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user) # Reduced cooldown for testing
    async def work(self, ctx):
        player = await players.find_one({"user_id": ctx.author.id})
        
        if not player:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Use `!start` first.")

        job_id = player.get("job", "unemployed")
        job_data = next((j for j in self.jobs if j["name"] == job_id), {"name": "Odd Jobs", "salary": 30})

        # --- MINI-GAME TRIGGER ---
        # Randomly choose which mini-game they have to play to finish the job
        game_choice = random.choice(["reaction", "typing"])
        
        if game_choice == "reaction":
            await ctx.send(f"🏢 **Work Task:** React to the emoji as fast as you can to finish your shift as a **{job_data['name'].title()}**!")
            game = ReactionGame()
            success = await game.start(ctx) # Assuming your game class has a .start() method
            
        else:
            await ctx.send(f"⌨️ **Work Task:** Type the sentence quickly to complete your work!")
            game = TypingGame()
            success = await game.start(ctx)

        # --- RESULT HANDLING ---
        if success:
            salary = job_data["salary"]
            await players.update_one(
                {"user_id": ctx.author.id},
                {"$inc": {"money": salary, "stats.reputation": 5}}
            )
            await ctx.send(f"✅ **Job Well Done!** You earned **${salary}** and **+5 Rep**.")
        else:
            await ctx.send(f"❌ **Shift Failed.** You messed up the task and didn't get paid this time. Try again later!")

    @work.error
    async def work_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Rest up! You can work again in {round(error.retry_after)} seconds.")

async def setup(bot):
    await bot.add_cog(Jobs(bot))
