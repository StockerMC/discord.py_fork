import discord

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

# setting `guild_ids` in development is better when possible because
# bulk overwriting global commands has a 1 hour delay
class Blep(discord.SlashCommand, guild_ids=[123]):
    """Send a random adorable animal photo"""

    animal: str = discord.application_command_option(description='The type of animal', choices=[
        discord.ApplicationCommandOptionChoice(name='Dog', value='animal_dog'),
        discord.ApplicationCommandOptionChoice(name='Cat', value='animal_cat'),
        discord.ApplicationCommandOptionChoice(name='Penguin', value='animal_penguin')
    ])

    async def callback(self, response: discord.SlashCommandResponse):
        photos = {
            'animal_dog': 'https://i.imgur.com/rpQdRoY.jpg',
            'animal_cat': 'https://pbs.twimg.com/media/E_hf3mzXsAQvIBq.jpg:large',
            'animal_penguin': 'https://static.onecms.io/wp-content/uploads/sites/20/2017/01/penguins.jpg',
        }

        photo = photos[response.options.animal]
        await response.send_message(photo)

client = MyClient()
client.add_application_command(Blep())
client.run('token')
