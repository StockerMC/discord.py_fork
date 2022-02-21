# Application Commands

Application commands in this libary are based on 

Examples can be found in the [examples/application_commands directory](examples/application_commands).

## Defining Commands

- To define a application command, subclass ``SlashCommand``, ``MessageCommand``, or ``UserCommand``.
- An application command must have a desdcription. This can be the docstring of the class or the ``description`` keyword argument.
- Arguments are passed to the class with keyword arguments inline with the class definition. For example:
```python
class Command(discord.SlashCommand, name='command_name'):
    """Command description"""
	...
```

## Registering Commands

During testing, it is recommended to set specific guilds that commands will be uploaded to speed up the process:
- The ``guild_ids`` keyword argument for the command class
- ``Client.application_command_guild_ids``
    * Added commands will be uploaded to these guilds if their ``guild_ids`` keyword argument was not set

To add a command to the bot, use the ``@client.application_command`` decorator on the class or use the ``client.add_application_command`` method. The ``client.add_application_command`` should be used if arguments need to be passed to the class.

The ``Client.register_application_commands_at_startup`` keyword argument is ``True`` by default. This calls the ``Client.register_application_commands_at_startup`` method when the bot starts up.

The ``Client.register_application_commands_at_startup`` method overrides ALL commands that have been uploaded with commands added to the bot.
- This method does not do anything if no commands were added to the bot.
- If a command has been uploaded but is not added to the bot when this is called, it will be removed.

## Command Options

- Options are defined by setting class variables with the ``application_command_option`` method.
	* It is required to set the ``description`` keyword argument.
- The variables can be annotated to set the type, or the ``type`` keyword argument can be passed.
- Options are required by default. To make an option optional:
    * Annotate it as ``Optional[T]`` with ``T`` being the type of the option
    * Or set the ``required`` keyword argument to ``False``.
	* The default value if the option is not provided is ``None``. For more information, see [Default Values](#default-values).

#### application_command_option
Parameters:
- ``description`` - The description of the option.
- ``name`` - The name of the option.
- ``type`` - The type of the option. This can be any of the option types and enum values in [Option Types](#option-types) and [Channel Types](#channel-types).
- ``required`` - Whether the option is required or not. Defaults to ``True``.
- ``default`` - See [Default Values](#default-values)
- ``channel_types`` - See [Channel Types](#channel-types)
- ``min_value`` - The minimum value permitted for this ``integer`` or ``number`` option.
- ``max_value`` - The maximum value permitted for this ``integer`` or ``number`` option.

### Option Types

Option types (excluding the types listed in [Channel Types](#channel-types)):

| Option Type    | Enum                                                 |
|----------------|------------------------------------------------------|
| ``str``        | ``discord.ApplicationCommandOptionType.string``      |
| ``int``        | ``discord.ApplicationCommandOptionType.integer``     |
| ``float``      | ``discord.ApplicationCommandOptionType.number``      |
| ``Member``     | ``discord.ApplicationCommandOptionType.user``        |
| ``User``       | ``discord.ApplicationCommandOptionType.user``        |
| ``Role``       | ``discord.ApplicationCommandOptionType.role``        |
| ``Object``     | ``discord.ApplicationCommandOptionType.mentionable`` |
| ``Attachment`` | ``discord.ApplicationCommandOptionType.attachment``  |

### Choices

Options can have specified choices for the user to select. To define choices, you can annotate the option with ``typing.Literal`` or set the ``choices`` keyword argument of ``application_command_option``. For example:
```python
class Animal(discord.SlashCommand):
    """Get an animal picture"""

    animal: typing.Literal['Dog', 'Cat', 'Penguin'] = discord.application_command_option(
        description='The type of animal',
    )
    # OR
    animal: str = discord.application_command_option(
        description='The type of animal',
        choices=['Dog', 'Cat', 'Penguin'],
    )
```

### Default Values

Default values can be set for optional options. To set a default value for an option, set the ``default`` keyword argument to the literal default value, or a coroutine function taking one argument, ``SlashCommandResponse``, that returns the default value. For example:
```python

```

### Channel Types

| Channel Type         | Enum                                             |
|----------------------|--------------------------------------------------|
| ``abc.GuildChannel`` | ``discord.ApplicationCommandOptionType.channel`` |
| ``TextChannel``      | ``discord.ChannelType.text``                     |
| ``VoiceChannel``     | ``discord.ChannelType.voice``                    |
| ``StageChannel``     | ``discord.ChannelType.stage_voice``              |
| ``CategoryChannel``  | ``discord.ChannelType.category``                 |
| ``Thread``           | ``discord.ChannelType.public_thread``            |

- ``abc.GuildChannel`` allows all types of channels to be selected.
- Multiple types can be specific by using ``typing.Union``:
```python
class Join(discord.SlashCommand):
    """Get the bot to join a channel"""

    channel: typing.Union[discord.VoiceChannel, discord.StageChannel] = discord.application_command_option(description='The channel to join')

    async def callback(self, response: discord.SlashCommandResponse):
        channel = response.options.channel
        await channel.connect()
        await response.send_message(f'Joined {channel.mention}')
```

### Autocomplete

- Options of type ``string``, ``integer``, and ``number`` can have an autocomplete callback.
- The choices returned or yielded from the callback must match the type of the option.

An autocomplete callback can be either of the following:
- A coroutine function that returns an iterable of strings, integers or floats.
- A coroutine function that returns an iterable of ``ApplicationCommandOptionChoice``.
- A coroutine function that yields strings, integers or floats.
- A coroutine function that yields ``ApplicationCommandOptionChoice`` objects.

This is an example of a slash command with autocompletion:

```python
FRUITS = [
    'Apple',
    'Banana',
    'Cherry',
    # ...
]

class Fruit(discord.SlashCommand):
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
```

## Subcommands & Subcommand Groups

To define a subcommand or subcommand group, set the ``parent`` keyword argument of the slash command to the parent class of the command.
- If you need to pass arguments to the parent class, use the ``set_parent`` method of the class instead.
- To indicate that a parent class is a group command, set the ``group`` keyword argument to ``True``.

Examples of command nesting:
```
VALID

command
|
|__ subcommand
|
|__ subcommand

----

VALID

command
|
|__ subcommand-group
    |
    |__ subcommand
|
|__ subcommand-group
    |
    |__ subcommand

----

VALID

command
|
|__ subcommand-group
    |
    |__ subcommand
|
|__ subcommand

-------

INVALID

command
|
|__ subcommand-group
    |
    |__ subcommand-group
|
|__ subcommand-group
    |
    |__ subcommand-group

----

INVALID

command
|
|__ subcommand
    |
    |__ subcommand-group
|
|__ subcommand
    |
    |__ subcommand-group
```

This is an example of correct nesting:
```python
class Permissions(discord.SlashCommand, guild_ids=[123]):
    ...

class User(discord.SlashCommand, parent=Permissions, group=True):
    ...

class Get(discord.SlashCommand, parent=User):
    ...

class Edit(discord.SlashCommand, parent=User):
    ...
```

This structure is equivalent to:
```
command
|
|__ subcommand-group
    |
    |__ subcommand
    |
    |__ subcommand
```
