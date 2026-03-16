import discord
from discord import app_commands
from discord.ext import commands
import json
import time
import random
from database.db import players
from systems.minigame_manager import MinigameManager

class JobDropdown(discord.ui.Select):
    def __init__(self, jobs, user_rep):
        self.jobs_list = jobs
        options = []
        for j in jobs:
            is_locked = user_rep < j.get('req_rep', 0)
            label = j['name'].replace('_', ' ').title()
            options.append(discord.SelectOption(
                label=label,
                description=f"Base: ${j['salary']} | Req: {j.get('req_rep', 0)} Rep",
                value=j['name'],
                emoji="🔒" if is_locked else "💼"
            ))
        super().__init__(placeholder="Choose your profession...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        job_id = self.values[0]
        job_data = next((j for j in self.jobs_list if j["name"] == job_id), None)
        
        player = await players.find_one({"user_id": interaction.user.id})
        user_rep = player.get("stats", {}).get("reputation", 0) if player else 0

        if user_rep < job_data.get('req_rep', 0):
            return await interaction.followup.send(f"❌ You need {job_data['req_rep']} Rep!", ephemeral=True)

        is_current_job = player.get("job") == job_id
        promo_level = player.get("job_level", 0) if is_current_job else 0
        
        self.view.current_selection = job_data
        self.view.update_buttons(is_current_job, promo_level)
        
        job_title = job_id.replace('_', ' ').title()
        if is_current_job and promo_level > 0:
            job_title = f"{job_data['promotions'][promo_level-1]}"

        embed = discord.Embed(title=f"💼 Job Info: {job_title}", color=discord.Color.blue())
        if "image" in job_data: embed.set_thumbnail(url=job_data["image"])

        promo_list = job_data.get("promotions", [])
        path_text = f"Entry Level: {job_id.replace('_', ' ').title()}\n"
        for i, p in enumerate(promo_list):
            check = "✅" if promo_level > i else "❌"
            path_text += f"Lvl {i+1}: {p} {check}\n"
        
        embed.add_field(name="📈 Career Progress", value=f"```\n{path_text}```", inline=False)
        
        salary = job_data['salary'] + (promo_level * 20)
        cooldown = job_data.get('cooldown', 300) + (promo_level * 60)
        
        embed.add_field(name="💰 Current Salary", value=f"${salary}", inline=True)
        embed.add_field(name="⏳ Cooldown", value=f"{cooldown//60}m", inline=True)

        await interaction.edit_original_response(embed=embed, view=self.view)

class JobView(discord.ui.View):
    def __init__(self, jobs_list, user_rep):
        super().__init__(timeout=60)
        self.jobs_list = jobs_list
        self.current_selection = None
        
        self.add_item(JobDropdown(jobs_list, user_rep))
        
        self.accept_btn = discord.ui.Button(label="Accept Job", style=discord.ButtonStyle.green, disabled=True)
        self.promote_btn = discord.ui.Button(label="Promote", style=discord.ButtonStyle.primary, emoji="⭐", disabled=True)
        
        self.accept_btn.callback = self.accept_callback
        self.promote_btn.callback = self.promote_callback
        
        self.add_item(self.accept_btn)
        self.add_item(self.promote_btn)

    def update_buttons(self, is_current, level):
        self.accept_btn.disabled = is_current
        self.promote_btn.disabled = not is_current or level >= 3

    async def accept_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await players.update_one(
            {"user_id": interaction.user.id}, 
            {"$set": {"job": self.current_selection['name'], "job_level": 0}}
        )
        await interaction.followup.send(f"✅ You started as a **{self.current_selection['name'].title()}**!")
        self.stop()

    async def promote_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        player = await players.find_one({"user_id": interaction.user.id})
        rep = player.get("stats", {}).get("reputation", 0)
        current_lvl = player.get("job_level", 0)
        
        req_rep = (current_lvl + 1) * 100
        if rep < req_rep:
            return await interaction.followup.send(f"❌ You need **{req_rep} Reputation** for a promotion!")

        await players.update_one(
            {"user_id": interaction.user.id},
            {"$inc": {"job_level": 1, "money": -50}}
        )
        new_title = self.current_selection['promotions'][current_lvl]
        await interaction.followup.send(f"🎊 Congratulations! You've been promoted to **{new_title}**!")
        self.stop()

class Jobs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mg_manager = MinigameManager()
        self.work_cooldowns = {}
        try:
            with open("assets/jobs.json") as f:
                self.jobs = json.load(f)
        except:
            self.jobs = [{"name": "laborer", "salary": 30, "req_rep": 0, "cooldown": 300, "promotions": []}]

    @commands.hybrid_command(name="jobs")
    async def jobs(self, ctx):
        player = await players.find_one({"user_id": ctx.author.id})
        if not player: return await ctx.send("❌ Use `/start` first.")
        
        view = JobView(self.jobs, player.get("stats", {}).get("reputation", 0))
        await ctx.send(embed=discord.Embed(title="💼 Job Board", color=discord.Color.blue()), view=view)

    @commands.hybrid_command(name="work")
    async def work(self, ctx):
        if ctx.interaction: await ctx.interaction.response.defer()
        
        player = await players.find_one({"user_id": ctx.author.id})
        if not player: return await ctx.send("❌ Use `/start` first.")

        job_id = player.get("job", "laborer")
        promo_level = player.get("job_level", 0)
        job_data = next((j for j in self.jobs if j["name"] == job_id), self.jobs[0])
        
        # Calculate Base Salary
        salary = job_data["salary"] + (promo_level * 20)
        
        # VAMPIRE BONUS LOGIC
        is_vampire = player.get("background") == "vampire"
        if is_vampire:
            salary = int(salary * 2)

        cooldown_time = job_data.get("cooldown", 300) + (promo_level * 60)

        last_work = self.work_cooldowns.get(ctx.author.id, 0)
        retry_after = last_work + cooldown_time - time.time()

        if retry_after > 0:
            return await ctx.send(f"⏳ Next shift in **{int(retry_after//60)}m {int(retry_after%60)}s**.")

        success = await self.mg_manager.run(ctx, job_data.get("minigame", "random"))

        if success:
            self.work_cooldowns[ctx.author.id] = time.time()
            await players.update_one(
                {"user_id": ctx.author.id},
                {"$inc": {"money": salary, "stats.reputation": 5}}
            )
            title = job_data['promotions'][promo_level-1] if promo_level > 0 else job_id.replace('_', ' ').title()
            
            bonus_text = " 🧛 (Vampire 2x Bonus!)" if is_vampire else ""
            await ctx.send(f"✅ **{title}** Shift Complete! Earned **${salary}**.{bonus_text}")
        else:
            await ctx.send("❌ Task failed!")

async def setup(bot):
    await bot.add_cog(Jobs(bot))
