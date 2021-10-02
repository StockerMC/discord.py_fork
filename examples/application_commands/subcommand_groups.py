import typing
import discord

class MyClient(discord.Client):
    def __init__(self):
        super().__init__()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

class AuthorDefault(discord.ApplicationCommandOptionDefault):
    async def default(self, response: discord.SlashCommandResponse):
        return response.user

# setting `guild_ids` in development is better when possible because
# registering global commands has a 1 hour delay
class Permissions(discord.SlashCommand, guild_ids=[123]):
    """Get or edit the permissions for a user or a role in the specified or current channel"""

class User(discord.SlashCommand, parent=Permissions, group=True):
    """Get or edit the permissions for a user or role in the specified or current channel"""

class Get(discord.SlashCommand, parent=User):
    """Get permissions for a user in the specified or current channel"""

    user: typing.Optional[discord.User] = discord.application_command_option(description='The user to get', default=AuthorDefault)

    async def callback(self, response: discord.SlashCommandResponse):
        user = response.options.user
        embed = discord.Embed(title=f'Permissions for {user}')
        for permission, value in response.channel.permissions_for(user):
            embed.add_field(name=permission.title().replace('_', ' '), value=value)

        await response.send_message(embed=embed, ephemeral=True)

client = MyClient()
# we can't use the `client.application_command` decorator for parent commands
client.add_application_command(Permissions())
client.run('token')
