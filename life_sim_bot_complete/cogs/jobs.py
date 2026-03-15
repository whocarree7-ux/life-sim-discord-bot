import discord
from discord.ext import commands
import json
from database.db import players
from systems.minigame_manager import MinigameManager

# This class handles the dropdown menu logic
class JobDropdown(discord.ui.Select):
    def __init__(self, jobs, user_rep):
        options = []
        for j in jobs:
            # Check if user has enough reputation
            is_locked = user_rep < j['req_rep']
            label = j['name'].replace('_', ' ').title()
            description = f"Salary: ${j['salary']} | Req: {j['req_rep']} Rep"
            
            options.append(discord.SelectOption(
                label=label,
                description=description,
                value=j['name'],
                emoji="🔒" if is_locked else "💼",
                default=False
            ))

        super().__init__(placeholder="Choose a profession...", min_values=1, max_values=1, options=options)
        self.jobs_data = jobs
        self.user_rep = user_rep

    async def callback(self, interaction: discord.Interaction):
        # Find the selected job data
        selected_job = next((j for j in self.jobs_data if j["name"] == self.values[0]), None)
        
        if self.user_rep < selected_job['req_rep']:
            await interaction.response.send_message(f"❌ You need **{selected_job['req_rep']} Rep** to become a {selected_job['name'].title()}!", ephemeral=True)
            return

        # Update Database
        await players.update_one(
            {"user_id": interaction.user.id},
            {"$set": {"job": selected_job['name']}}
        )
        
        await interaction.response.send_message(f"💼 You are now a **{selected_job['name'].replace('_', ' ').title()}**!", ephemeral=True)

class JobView(discord.ui.View):
    def __init__(self, jobs, user_rep):
        super().__init__()
        self.add_item(JobDropdown(jobs, user_rep))

class Jobs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mg_manager = MinigameManager()
        try:
            with open("assets/jobs.json") as f:
                self.jobs = json.load(f)
        except:
            self.jobs = [{"name": "laborer", "salary": 30, "req_rep": 0, "minigame": "random"}]

    @commands.command(name="jobs")
    async def jobs_menu(self, ctx):
        """Shows the interactive job selection menu."""
        player = await players.find_one({"user_id": ctx.author.id})
        if not player:
            return await ctx.send("❌ Use `!start` first.")

        user_rep = player.get("stats", {}).get("reputation", 0)
        
        embed = discord.Embed(
            title="💼 Profession Center", 
            description="Select a job from the menu below to start your career!",
            color=discord.Color.blue()
        )
        embed.add_field(name="Your Reputation", value=f"⭐ {user_rep}")
        embed.set_footer(text="Higher reputation unlocks better paying jobs.")

        view = JobView(self.jobs, user_rep)
        await ctx.send(embed=embed, view=view)

    @commands.command()
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def work(self, ctx):
        player = await players.find_one({"user_id": ctx.author.id})
        if not player:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Use `!start` first.")

        job_id = player.get("job", "laborer")
        job_data = next((j for j in self.jobs if j["name"] == job_id), self.jobs[0])
        target_game = job_data.get("minigame", "random")
        
        await ctx.send(f"⚒️ **Work Shift:** Preparing your task for **{job_data['name'].replace('_', ' ').title()}**...")
        
        success = await self.mg_manager.run(ctx, target_game)

        if success:
            salary = job_data["salary"]
            await players.update_one(
                {"user_id": ctx.author.id},
                {"$inc": {"money": salary, "stats.reputation": 5}}
            )
            await ctx.send(f"✅ **Shift Complete!** You earned **${salary}** and **+5 Rep**.")
        else:
            await ctx.send(f"❌ **Shift Failed!** Better luck next time.")

async def setup(bot):
    await bot.add_cog(Jobs(bot))
