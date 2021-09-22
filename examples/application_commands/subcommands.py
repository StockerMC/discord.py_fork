import discord

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

# setting `guild_ids` in development is better when possible because
# bulk overwriting global commands has a 1 hour delay
class Show(discord.SlashCommand, guild_ids=[123]):
    """Get or edit permissions for a user or a role in the current channel"""

class Channels(discord.SlashCommand, parent=Show):
    """Get or edit permissions for a user in the current channel"""

    async def callback(self, response: discord.SlashCommandResponse):
        channels = '\n'.join([channel.mention for channel in response.guild.channels])
        embed = discord.Embed(description=channels)
        await response.send_message(embed=embed, ephemeral=True)

class Roles(discord.SlashCommand, parent=Show):
    """Get permissions for a user in the current channel"""

    async def callback(self, response: discord.SlashCommandResponse):
        roles = '\n'.join([role.mention for role in response.guild.roles])
        embed = discord.Embed(description=roles)
        await response.send_message(embed=embed, ephemeral=True)

client = MyClient()
client.add_application_command(Show())
client.run('token')
