import discord

class MyClient(discord.Client):
    def __init__(self):
        super().__init__()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

# setting `guild_ids` in development is better when possible because
# registering global commands has a 1 hour delay
class Info(discord.UserCommand, guild_ids=[123]):
    async def callback(self, response: discord.UserCommandResponse):
        # the target for a UserCommand is the user who the command was used on
        user = response.target
        avatar = response.target.display_avatar.url
        await response.send_message(f'{user.mention} -- {user.id}\n{avatar}', ephemeral=True)

client = MyClient()
client.add_application_command(Info())
client.run('token')
