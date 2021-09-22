import discord

class MyClient(discord.Client):
    def __init__(self):
        # setting the application_id kwarg is required when
        # registering application commands
        super().__init__(application_id=123)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

# setting `guild_ids` in development is better when possible because
# bulk overwriting global commands has a 1 hour delay
class Info(discord.MessageCommand, guild_ids=[123]):
    async def callback(self, response: discord.MessageCommandResponse):
        # the target of a MessageCommand is the message the command was used on
        message = response.target
        content = message.content
        author = response.target.author
        await response.send_message(f'Message by {author.mention}: {content}', ephemeral=True)

client = MyClient()
client.add_application_command(Info())
client.run('token')
