import typing
import discord

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

client = MyClient()

# setting `guild_ids` in development is better when possible because
# registering global commands has a 1 hour delay
@client.application_command
class Avatar(discord.SlashCommand, guild_ids=[123]):
    """Get the avatar of the provided user or yourself"""

    # the `required` kwarg keyword argument can also be set to `False`
    # instead of typehinting the argument as optional
    user: typing.Optional[discord.User] = discord.application_command_option(
        description='The user to get the avatar from',
        # the default callback can also be a coroutine function
        default=lambda response: response.user,
    )

    async def callback(self, response: discord.SlashCommandResponse):
        avatar = response.options.user.display_avatar.url
        await response.send_message(avatar, ephemeral=True)

client.run('token')
