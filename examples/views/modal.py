from typing import Union
from discord.ext import commands

import discord

class QuestionsBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('$'))

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


class QuestionsModal(discord.ui.Modal):
    def __init__(self, user: Union[discord.User, discord.Member]):
        children = [
            discord.ui.InputText(label='What is your favourite colour?', style=discord.InputTextStyle.short),
            discord.ui.InputText(label='What is your favourite animal?', style=discord.InputTextStyle.short),
            discord.ui.InputText(label='What are your favourite countries?',style=discord.InputTextStyle.paragraph),
        ]

        super().__init__(title=f'{user.display_name}\'s Questionnaire', children=children)

    async def callback(self, interaction: discord.Interaction) -> None:
        message = f'Your favourite colour is **{self.values[0]}**!\n'
        message += f'Your favourite animal is **{self.values[1]}**!\n'
        favourite_countries = len(self.values[3].split("\n"))
        message += f'You have **{favourite_countries}** favourite countries!'
        await interaction.response.send_message(message, ephemeral=True)

class QuestionsView(discord.ui.View):
    @discord.ui.button(label='Start', style=discord.ButtonStyle.green)
    async def start(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(QuestionsModal(interaction.user))


bot = QuestionsBot()

@bot.command()
async def start(ctx: commands.Context):
    """Starts a questionnaire from the bot."""
    await ctx.send('Press!', view=QuestionsView())

bot.run('token')
