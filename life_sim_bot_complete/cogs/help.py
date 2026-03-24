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
**/bank** - View your balance and credit score
**/deposit** - Move cash to your secure bank account
**/withdraw** - Take money out for spending
**/loan** - Request a bank loan
**/repay** - Pay off your outstanding debt
**/pay** - Transfer money to another player
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
**/market** - View the current stock/crypto market
**/buy** - Purchase assets using bank funds
**/sell** - Sell your assets for a profit
""",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed)

    # CRIME
    @discord.ui.button(label="Crime", style=discord.ButtonStyle.danger, emoji="🧨")
    async def crime(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🧨 Criminal Activities",
            description="""
**/crime** - Commit a random street crime
**/steal** - Attempt to rob another player
**/hack** - Breach mainframes (Rewards based on Intelligence)
**/heist** - High-risk bank robbery
*Warning: Crimes reduce your Reputation!*
""",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed)

    # JOBS
    @discord.ui.button(label="Jobs", style=discord.ButtonStyle.gray, emoji="💼")
    async def jobs(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="💼 Job Commands",
            description="""
**/jobs** - Browse the job board
**/work** - Complete a shift (Uses Energy ⚡)
""",
            color=discord.Color.dark_gray()
        )
        await interaction.response.edit_message(embed=embed)

    # PROFILE & HOUSING
    @discord.ui.button(label="Profile", style=discord.ButtonStyle.blurple, emoji="👤")
    async def profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="👤 Profile & Lifestyle",
            description="""
**Character Stats:**
`/start`, `/profile`, `/daily`

**Housing:**
`/house`, `/house buy`, `/house upgrade`, `/house invite`
""",
            color=discord.Color.blurple()
        )
        await interaction.response.edit_message(embed=embed)


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show the Omnix Island help menu")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🌌 Omnix Island Help Menu",
            description="Select a category below to explore the island's features.",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="Categories",
            value="""
💰 **Economy** - Banking & Transfers
📈 **Investments** - Markets & Trading
🧨 **Crime** - High-risk activities
💼 **Jobs** - Career & Energy
👤 **Profile** - Stats & Housing
""",
            inline=False
        )

        embed.set_footer(text="Omnix Island • Choose your path")
        await interaction.response.send_message(embed=embed, view=HelpView())


async def setup(bot):
    await bot.add_cog(Help(bot))