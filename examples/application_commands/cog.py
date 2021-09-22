import discord
from discord.ext import commands

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!')

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

# setting `guild_ids` in development is better when possible because
# bulk overwriting global commands has a 1 hour delay
class Hello(discord.SlashCommand, guild_ids=[123]):
    """Say hello!"""

    def __init__(self, cog):
        self.cog = cog

    async def callback(self, response: discord.SlashCommandResponse):
        message = f'Hello {response.user.name}!'
        last_user = self.cog.last_user
        if last_user:
            message += f' {last_user.name} said hello last!'
        await response.send_message(message, ephemeral=True)

class Fun(commands.Cog):
    def __init__(self):
        self.last_user = None
        self.add_application_command(Hello(self))

    @commands.command()
    async def hello(self, ctx: commands.Context):
        await ctx.send(f'Hello {ctx.author.name}!', mention_author=True)
        self.last_user = ctx.author

bot = MyBot()
bot.add_cog(Fun())
bot.run('token')
