import typing
import discord

class MyClient(discord.Client):
    def __init__(self):
        # setting the application_id kwarg is required when
        # registering application commands
        super().__init__(application_id=123)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

class AuthorDefault(discord.ApplicationCommandOptionDefault):
    async def default(self, response: discord.SlashCommandResponse):
        return response.user

# setting `guild_ids` in development is better when possible because
# registering global commands has a 1 hour delay
class Hello(discord.SlashCommand, guild_ids=[123]):
    """Say hello to someone!"""

    user: typing.Optional[discord.User] = discord.application_command_option(description='The user to say hello to', default=AuthorDefault)

    async def callback(self, response: discord.SlashCommandResponse):
        await response.send_message(f'Hello, {response.options.user.name}!')

client = MyClient()
client.add_application_command(Hello())
client.run('token')
