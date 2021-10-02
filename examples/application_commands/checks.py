import discord

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

class Cool(discord.SlashCommand):
    """For cool people only"""

    def __init__(self, client: MyClient):
        self.client = client

    async def command_check(self, response: discord.SlashCommandResponse):
        if await self.client.is_owner(response.user):
            return True
        else:
            await response.send_message("You aren't cool enough to use this!")
            return False

    async def callback(self, response: discord.SlashCommandResponse):
        await response.send_message(f'{response.user.name} is cool!')

class Ban(discord.SlashCommand):
    """Ban a member from the server"""

    member: discord.Member = discord.application_command_option(description='The member to ban')

    async def command_check(self, response: discord.SlashCommandResponse):
        # check if the person who used the command has the ban members permissions
        if response.channel.permissions_for(response.user).ban_members:
            return True
        else:
            await response.send_message("You can't ban members!")
            return False

    async def callback(self, response: discord.SlashCommandResponse) -> None:
        await response.send_message(f'{response.user.name} banned {response.options.member}')

class Moderation(discord.Cog):
    def __init__(self):
        self.add_application_command(Ban())

    async def cog_application_command_check(self, response: discord.SlashCommandResponse):
        # check if someone named pikaninja used the command
        if response.user.name == 'pikaninja':
            await response.send_message("pikaninja can't ban members!")
            return False

        return True

# we set the `application_command_guild_ids` kwarg so
# we don't have to set the `guild_ids` kwarg for all commands.
# setting `guild_ids` per command or for all commands in development is better
# when possible because registering global commands has a 1 hour delay
client = MyClient(application_command_guild_ids=[123])

# a global check for our application commands
# response will always be a `SlashCommandResponse` in this example 
# because we only have slash commands registered
@client.application_command_check
async def in_testing(response: discord.SlashCommandResponse):
    # check if the application command was used in a channel named testing
    if response.channel.name == 'testing':
        return True
    else:
        await response.send_message(f"You can't use the {response.command} command here!")
        return False

client.add_cog(Moderation())
client.add_application_command(Cool(client))
client.run('token')
