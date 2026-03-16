import discord
from discord.ext import commands
from discord import app_commands


class HelpView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    # ECONOMY
    @discord.ui.button(label="Economy", style=discord.ButtonStyle.green, emoji="💰")
    async def economy(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = discord.Embed(
            title="💰 Economy Commands",
            description="""
/bank
/deposit
/withdraw
/loan
/repay
""",
            color=discord.Color.green()
        )

        await interaction.response.edit_message(embed=embed)

    # INVESTMENTS
    @discord.ui.button(label="Investments", style=discord.ButtonStyle.blurple, emoji="📈")
    async def investments(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = discord.Embed(
            title="📈 Investment Commands",
            description="""
/market
/buy
/sell
""",
            color=discord.Color.blue()
        )

        await interaction.response.edit_message(embed=embed)

    # JOBS
    @discord.ui.button(label="Jobs", style=discord.ButtonStyle.gray, emoji="💼")
    async def jobs(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = discord.Embed(
            title="💼 Job Commands",
            description="""
/jobs
/work
""",
            color=discord.Color.dark_gray()
        )

        await interaction.response.edit_message(embed=embed)

    # PROFILE
    @discord.ui.button(label="Profile", style=discord.ButtonStyle.blurple, emoji="👤")
    async def profile(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = discord.Embed(
            title="👤 Profile Commands",
            description="""
/profile
/start
""",
            color=discord.Color.blurple()
        )

        await interaction.response.edit_message(embed=embed)

    # HOUSING
    @discord.ui.button(label="Housing", style=discord.ButtonStyle.green, emoji="🏠")
    async def housing(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = discord.Embed(
            title="🏠 Housing Commands",
            description="""
/house
/house buy
/house invite
/house decor
/house upgrade
""",
            color=discord.Color.gold()
        )

        await interaction.response.edit_message(embed=embed)


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show the Omnix Island help menu")
    async def help(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="🌌 Omnix Island Help Menu",
            description="Use the buttons below to explore commands.",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="Categories",
            value="""
💰 Economy
📈 Investments
💼 Jobs
👤 Profile
🏠 Housing
""",
            inline=False
        )

        embed.set_footer(text="Omnix Island • Adventure Awaits")

        await interaction.response.send_message(embed=embed, view=HelpView())


async def setup(bot):
    await bot.add_cog(Help(bot))