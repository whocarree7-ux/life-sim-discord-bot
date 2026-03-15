import discord
from discord import app_commands
from discord.ext import commands
import json
import random
from database.db import players
from systems.minigame_manager import MinigameManager

class JobDropdown(discord.ui.Select):
    def __init__(self, jobs, user_rep):
        options = []
        for j in jobs:
            is_locked = user_rep < j.get('req_rep', 0)
            label = j['name'].replace('_', ' ').title()
            options.append(discord.SelectOption(
                label=label,
                description=f"Salary: ${j['salary']} | Req: {j.get('req_rep', 0)} Rep",
                value=j['name'],
                emoji="🔒" if is_locked else "💼"
            ))
        super().__init__(placeholder="Choose your profession...", options=options)

    async def callback(self, interaction: discord.Interaction):
        job_id = self.values[0]
        job_data = next((j for j in self.view.jobs_list if j["name"] == job_id), None)
        
        player = await players.find_one({"user_id": interaction.user.id})
        user_rep = player.get("stats", {}).get("reputation", 0) if player else 0

        if user_rep < job_data.get('req_rep', 0):
            return await interaction.response.send_message(f"❌ You need {job_data['req_rep']} Rep!", ephemeral=True)

        # Update Database
        await players.update_one(
            {"user_id": interaction.user.id},
            {"$set": {"job": job_id}}
        )

        # Create a beautiful detailed description embed
        job_title = job_id.replace('_', ' ').title()
        embed = discord.Embed(
            title=f"✅ Job Selected: {job_title}",
            description=f"Congratulations! You are now working as a **{job_title}**.\nUse `/work` to start your shift.",
            color=discord.Color.green()
        )

        # Check for image in JSON
        if "image" in job_data:
            embed.set_thumbnail(url=job_data["image"])

        embed.add_field(name="💰 Base Salary", value=f"${job_data['salary']}", inline=True)
        embed.add_field(name="⭐ Rep Gain", value="+5 Points", inline=True)
        embed.add_field(name="⏳ Cooldown", value="5 Minutes", inline=True)
        embed.add_field(name="🎮 Minigame", value=f"{job_data.get('minigame', 'Standard').title()}", inline=True)
        
        embed.set_footer(text="Arcadia Employment Services")

        # Edit the original message to show the description and remove the dropdown
        await interaction.response.edit_message(embed=embed, view=None)
        
        # Keep the success prompt as a small temporary message
        await interaction.followup.send(f"✅ Success! You are now a **{job_title}**.", ephemeral=True)

class JobView(discord.ui.View):
    def __init__(self, jobs_list, user_rep):
        super().__init__(timeout=60)
        self.jobs_list = jobs_list
        self.add_item(JobDropdown(jobs_list, user_rep))

class Jobs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mg_manager = MinigameManager()
        try:
            with open("assets/jobs.json") as f:
                self.jobs = json.load(f)
        except Exception as e:
            print(f"JSON Error: {e}")
            self.jobs = [{"name": "laborer", "salary": 30, "req_rep": 0, "minigame": "reaction"}]

    @commands.hybrid_command(name="jobs", description="View and select available jobs")
    async def jobs(self, ctx):
        player = await players.find_one({"user_id": ctx.author.id})
        if not player:
            return await ctx.send("❌ Use `!start` first.")

        user_rep = player.get("stats", {}).get("reputation", 0)
        view = JobView(self.jobs, user_rep)
        
        embed = discord.Embed(title="💼 Job Board", description="Select a job below:", color=discord.Color.blue())
        embed.set_footer(text=f"Your Reputation: {user_rep}")
        
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="work", description="Work your shift to earn money")
    @commands.cooldown(1, 300, commands.BucketType.user) 
    async def work(self, ctx):
        player = await players.find_one({"user_id": ctx.author.id})
        if not player:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Use `!start` first.")

        job_id = player.get("job", "laborer")
        job_data = next((j for j in self.jobs if j["name"] == job_id), self.jobs[0])
        
        await ctx.send(f"⚒️ **Work Shift:** {job_data['name'].replace('_', ' ').title()} task starting...")
        
        success = await self.mg_manager.run(ctx, job_data.get("minigame", "random"))

        if success:
            salary = job_data["salary"]
            await players.update_one(
                {"user_id": ctx.author.id},
                {"$inc": {"money": salary, "stats.reputation": 5}}
            )
            await ctx.send(f"✅ Shift Complete! Earned **${salary}** and **+5 Rep**.")
        else:
            await ctx.send("❌ Shift Failed! You didn't finish the task.")

    @work.error
    async def work_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            minutes = int(error.retry_after // 60)
            seconds = int(error.retry_after % 60)
            await ctx.send(f"⏳ **Chill out!** You are tired. You can work again in **{minutes}m {seconds}s**.")
        else:
            raise error

async def setup(bot):
    await bot.add_cog(Jobs(bot))
