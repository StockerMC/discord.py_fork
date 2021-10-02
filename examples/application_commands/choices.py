import typing
import discord

class MyClient(discord.Client):
    def __init__(self):
        super().__init__()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

client = MyClient()

# setting `guild_ids` in development is better when possible because
# registering global commands has a 1 hour delay
@client.application_command
class Blep(discord.SlashCommand, guild_ids=[123]):
    """Send a random adorable animal photo"""

    # if we wanted the values to be different than the name, we would
    # pass our own discord.ApplicationCommandOptionChoice instances to
    # the choices parameter of application_command_option (which takes a list)
    animal: typing.Optional[typing.Literal['Dog', 'Cat', 'Penguin']] = discord.application_command_option(
        description='The type of animal',
        default='Dog',
    )

    async def callback(self, response: discord.SlashCommandResponse):
        photos = {
            'Dog': 'https://i.imgur.com/rpQdRoY.jpg',
            'Cat': 'https://pbs.twimg.com/media/E_hf3mzXsAQvIBq.jpg:large',
            'Penguin': 'https://static.onecms.io/wp-content/uploads/sites/20/2017/01/penguins.jpg',
        }

        photo = photos[response.options.animal]
        await response.send_message(photo)

client.run('token')
