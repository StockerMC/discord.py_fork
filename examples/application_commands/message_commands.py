import discord

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

client = MyClient()

# setting `guild_ids` in development is better when possible because
# registering global commands has a 1 hour delay
@client.application_command
class Info(discord.MessageCommand, guild_ids=[123]):
    async def callback(self, response: discord.MessageCommandResponse):
        # the target of a MessageCommand is the message the command was used on
        message = response.target
        content = message.content
        author = response.target.author
        await response.send_message(f'Message by {author.mention}: {content}', ephemeral=True)

client.run('token')
