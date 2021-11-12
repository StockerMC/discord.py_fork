import typing
import discord

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

FRUITS = [
    'Apple',
    'Pear',
    'Banana',
    'Orange',
    'Blueberry',
    'Grapefruit',
    'Blackberry',
    'Strawberry',
    'Cherry',
    'Lemon',
    'Peach',
    'Passionfruit',
]

client = MyClient()

# setting `guild_ids` in development is better when possible because
# registering global commands has a 1 hour delay
@client.application_command
class Fruit(discord.SlashCommand, guild_ids=[123]):
    """Choose a fruit!"""

    # we set the type kwarg instead of typehinting to avoid type checker errors
    # when using the `autocomplete` decorator
    fruit = discord.application_command_option(description='The fruit to choose', type=str)

    # this function must be async and can also return an iterable of strings, integers or floats
    @fruit.autocomplete
    async def fruit_autocomplete(self, response: discord.AutocompleteResponse) -> typing.AsyncIterator[str]:
        for fruit in FRUITS:
            if response.value.lower() in fruit.lower():
                yield fruit

    async def callback(self, response: discord.SlashCommandResponse):
        fruit = response.options.fruit
        lowered = map(str.lower, FRUITS)
        if fruit.lower() not in lowered:
            await response.send_message(f"I don't know much about {fruit}.")
        else:
            await response.send_message(f'I like {fruit} too!')

client.run('token')
