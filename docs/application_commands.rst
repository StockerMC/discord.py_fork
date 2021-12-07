Application Commands
====================

Application commands are based on the class based implementation of the `slash command DSL <https://gist.github.com/Rapptz/2a7a299aa075427357e9b8a970747c2c>`_ Rapptz made.

Examples of application commands and topics covered can be found in the `examples/application_commands <https://github.com/StockerMC/discord.py/tree/master/examples/application_commands>`_ directory.

There are three classes you can derive from for making application commands. Keyword arguments are passed to them through the class declaration instead of through the ``__init__`` of the class.
The classes and the keyword arguments each of them take are as follows:

* ``discord.SlashCommand``

  * name: ``str`` - The name of the slash command. This defaults to the name of the class.
  * description: ``str`` - The description of the slash command. This is required.
  * guild_ids: ``Optional[List[int]]`` - The IDs of the guilds to upload the slash command to. **It is recommended to set this while testing to speed up the registering of the command**. Defaults to ``None``.
  * global_command: ``bool`` - Whether the slash command is a global command. Defaults to ``True``.
  * default_permission: ``bool`` - Whether the slash command is enabled by default when the application is added to a guild. Defaults to ``True``.
  * parent: ``discord.SlashCommand`` - The parent slash command of this slash command.
  * group: ``bool``- Whether the slash command is a group command.
* ``discord.MessageCommand``

  * name: ``str`` - The name of the message command. This defaults to the name of the class.
* ``discord.UserCommand``

  * name: ``str`` - The name of the user command. This defaults to the name of the class.

Application Command Options
===========================

Slash commands are the only application command that can have options currently.
To create an application command option, use ``discord.application_command_option``:

Used for creating an option for an application command.

To avoid type checker errors when using this with typehints,
the return type is ``Any`` if the ``type`` parameter is not
set.

.. note::

    If this is used in a class with a channel typehint (excluding ``.abc.GuildChannel``),
    the channel types of the option will be set to the class being typehinted. In the case of a
    ``typing.Union`` typehint of channel types, the channel types of the option will be set
    to that.

**Parameters**

* description: ``str`` - The description of the option.
* name: ``str`` - The name of the option.
* type: ``Union[discord.ApplicationCommandOptionType, Type]`` - The type of the option. This can be an ``ApplicationCommandOptionType`` member or a Discord model. Note that not all Discord models are acceptable types.
* required: ``bool`` - Whether the option is required or not. Defaults to ``True``.
* choices: ``Optional[Iterable[discord.ApplicationCommandOptionChoice]]`` - The choices of the option, if any.
* default: ``Optional[Union[discord.ApplicationCommandOptionDefault, Type[discord.ApplicationCommandOptionDefault]]]`` - The default of the option for when it's accessed with its relevant ``ApplicationCommandOptions`` instance.
* channel_types: ``Iterable[Union[discord.ChannelType, Type]]``- The valid channel types for this option. This is only valid for options of type ``ApplicationCommandOptionType.channel``. This can including the following: ``ChannelType`` members, ``TextChannel``, ``VoiceChannel``, ``StageChannel``, ``CategoryChannel`` and ``Thread``.
* min_value: ``Optional[int]`` - The minimum value permitted for this option. This is only valid for options of type ``ApplicationCommandOptionType.integer``.
* max_value: ``Optional[int]`` The maximum value permitted for this option. This is only valid for options of type ``ApplicationCommandOptionType.integer``.

**Returns**

``discord.ApplicationCommandOption`` - The created application command option.

``discord.ApplicationCommandOption``
------------------------------------

``discord.application_command_option`` should be used to create options, not this class.

* type: ``discord.ApplicationCommandOptionType`` - The type of the option.
* name: ``str`` - The name of the option.
* description: ``str`` - The description of the option.
* required: ``bool`` - Whether the option is required or not.
* choices: ``List[discord.ApplicationCommandOptionChoice]`` - The choices of the option.
* options: ``List[discord.ApplicationCommandOption]`` - The parameters of the option if its ``type`` is ``ApplicationCommandOptionType.sub_command`` or ``ApplicationCommandOptionType.sub_command_group``.
* default: ``Optional[Union[discord.ApplicationCommandOptionDefault, Any]]``- The default for the option, if any. This is for when the option is accessed with it's relevant ``ApplicationCommandOptions`` instance and the option was not provided by the user.
* channel_types: ``Set[discord.ChannelType]`` - The valid channel types for this option. This is only valid for options of type ``ApplicationCommandOptionType.channel``.
* min_value: ``Optional[int]`` - The minimum value permitted for this option. This is only valid for options of type ``ApplicationCommandOptionType.integer``.
* max_value: ``Optional[int]`` - The maximum value permitted for this option. This is only valid for options of type ``ApplicationCommandOptionType.integer``.
* ``@autocomplete`` - The callable for responses to when a user is typing an autocomplete option. This can be a ``typing.AsyncIterator`` that yields choices with types of ``str``, ``int`` or ``float``. This can also be a coroutine function that returns an iterable of choices with types of ``str``, ``int`` or ``float``. Similar to an application command's ``command_check``, it takes a single parameter which is the response from a user typing the option.

Application Command Option Choices
----------------------------------

To set the choices of an application command option, pass a list of ``ApplicationCommandOptionChoice`` objects to the ``choices`` keyword argument.
Only options of type ``str``, ``int``, and ``float`` can have choices. The type of the value of the choices of the option must be the same as the type of the option as well.
If an option is type hinted with ``typing.Literal``, each type argument of the ``Literal`` is set as a choice of the option, being the name and value of the option choice.

Quick example:

.. code-block python3

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

``discord.ApplicationCommandOptionChoice``

* name: ``str`` - The name of the choice. This is shown to users.
* value: ``Union[str, int, float]`` - The value of the choice. This is what you will receive if the choice is selected. The type of this should be the same type of the option it is for.

Application Command Option Defaults
-----------------------------------

The ``default`` keyword argument of ``application_command_option`` can either be a literal, or a class or class instance that derives from ``ApplicationCommandOptionDefault`` and overrides the ``default`` method (which must be a coroutine function).

For example:

.. code-block python3

    class AuthorDefault(discord.ApplicationCommandOptionDefault):
        async def default(self, response: discord.SlashCommandResponse):
            return response.user

    class Avatar(discord.SlashCommand):
        """Get the avatar of the provided user or yourself"""

        user: discord.User = discord.application_command_option(description='The user to get the avatar from', default=AuthorDefault)

        async def callback(self, response: discord.SlashCommandResponse):
            ...

If the ``user`` option is not provided by the user, ``response.options.user`` will be the user who used the command.

We can also set the default to a literal value:

.. code-block python3

    class News(discord.SlashCommand):
        """Get the major news stories of the provided year, or 2021"""

        year: typing.Optional[int] = discord.application_command_option(
            description='The year',
            default=2021,
        )

        async def callback(self, response: discord.SlashCommandResponse):
            ...

Application Command Option Channel Types
----------------------------------------

If you have the type hint or ``type`` kwarg of an option set to a channel type, only channels of that type will be valid for the user to provide. There are multiple ways to set the required channel types for an option:

``discord.abc.GuildChannel`` as a type or type hint sets the type of the option to a channel type, without setting any required channel types.

.. code-block python3

    option: discord.TextChannel = discord.application_command_option(description='A text channel')
    # or
    option = discord.application_command_option(description='A text channel', type=discord.TextChannel)

    # ...

    option: typing.Union[
        discord.TextChannel, discord.VoiceChannel
    ] = discord.application_command_option(description='A text or voice channel')
    # or
    option = discord.application_command_option(description='A text or voice channel', type=discord.abc.GuildChannel, channel_types=[
        discord.TextChannel, discord.VoiceChannel
    ])

Valid Channel Types
-------------------

Note that other ``discord.ChannelType`` members that are not listed here are valid.

+------------------+--------------------------------+
| Channel Type     | ``discord.ChannelType``        |
+==================+================================+
| TextChannel      | ``ChannelType.text``           |
+------------------+--------------------------------+
| VoiceChannel     | ``ChannelType.voice``          |
+------------------+--------------------------------+
| StageChannel     | ``ChannelType.stage_voice``    |
+------------------+--------------------------------+
| CategoryChannel  | ``ChannelType.category``       |
+------------------+--------------------------------+
| Thread           | ``ChannelType.public_thread``  |
+------------------+--------------------------------+

All Valid Option Types (Excluding Channel Types)
------------------------------------------------

+---------------------+-----------------------------------------------+-------------------------------------+
| Option Type         | ``discord.ApplicationCommandOptionType``      | Note                                |
+=====================+===============================================+=====================================+
| ``str``             | ``ApplicationCommandOptionType.string``       |                                     |
+---------------------+-----------------------------------------------+-------------------------------------+
| ``int``             | ``ApplicationCommandOptionType.integer``      | Any integer between -2^53 and 2^53  |
+---------------------+-----------------------------------------------+-------------------------------------+
| ``float``           | ``ApplicationCommandOptionType.number``       | Any double between -2^53 and 2^53   |
+---------------------+-----------------------------------------------+-------------------------------------+
| ``bool``            | ``ApplicationCommandOptionType.boolean``      |                                     |
+---------------------+-----------------------------------------------+-------------------------------------+
| ``discord.User``    | ``ApplicationCommandOptionType.user``         | Same as ``discord.Member``          |
+---------------------+-----------------------------------------------+-------------------------------------+
| ``discord.Member``  | ``ApplicationCommandOptionType.user``         | Same as ``discord.User``            |
+---------------------+-----------------------------------------------+-------------------------------------+
| ``discord.Role``    | ``ApplicationCommandOptionType.role``         |                                     |
+---------------------+-----------------------------------------------+-------------------------------------+
| ``discord.Object``  | ``ApplicationCommandOptionType.mentionable``  | Includes users and roles            |
+---------------------+-----------------------------------------------+-------------------------------------+


Application Command Responses
=============================

The callback of application commands receive one argument: the response of the command used. All response types inherit all the attributes, properties and methods as ``discord.Interaction`` and ``discord.InteractionResponse``. The listed attributes of the response types do not include them.

.. note::

    All response types are generic for the type of ``response.client`` (which is the same as ``response.interaction.client``), which means you can type hint it like so:

    .. code-block python3

        async def callback(self, response: discord.SlashCommandResponse[discord.Client]):
            # your type checker would now know that the type of response.client/response.interaction.client is discord.Client

Slash Commands
--------------

* ``discord.SlashCommandResponse``

  * interaction: ``discord.Interaction`` - The interaction of the response
  * options: ``discord.ApplicationCommandOptions`` - The options of the slash command used.
  * command: ``discord.SlashCommand`` - The slash command used.

``discord.ApplicationCommandOptions``
-------------------------------------

The attributes of ``discord.ApplicationCommandOptions`` instances are set based on the options of the slash command.

If an option is optional **without a default** and it was not provided by the user, it will be set as ``None``.
If an option is optional **with a literal default** and it was not provided by the user, it will be set as that default.
If an option is optional **with a** ``discord.ApplicationCommandOptionDefault`` **subclass** and it was not provided by the user, it will be set as the result of its ``default`` method.

Operations:

* ``x == y`` - Checks if two ``ApplicationCommandOptions`` are equal. This checks if both instances have the same provided options with the same values.

* ``x != y`` - Checks if two ``ApplicationCommandOptions`` are not equal.

* ``bool(x)`` - Returns whether any options were provided.

* ``hash(x)`` - Return the ``ApplicationCommandOptions``'s hash.

* ``iter(x)`` - Returns an iterator of ``(option, value)`` pairs. This allows it to be, for example, constructed as a dict or a list of pairs.

* ``len(x)`` - Returns the number of options provided.

* ``y in x`` - Checks if the option name ``y`` was provided.

Slash Command Subcommands and Subcommand Groups
-----------------------------------------------

This was taken from the `discord developer docs <https://discord.com/developers/docs/interactions/application-commands#subcommands-and-subcommand-groups>`_:

    We support nesting one level deep within a group, meaning your top level command can contain subcommand groups, and those groups can contain subcommands. That is the only kind of nesting supported. Here's some visual examples:

    .. code-block:: text
    
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


An example of a valid subcommand structure:

.. code-block:: python3

    class Docs(discord.SlashCommand):
        ...

    class Python(discord.SlashCommand, parent=Docs):
        ...

    class Rust(discord.SlashCommand, parent=Docs):
        ...

.. code-block:: text

    docs
    |
    |__ python
    |
    |__ rust

An example of an invalid subcommand structure:

.. code-block:: python3

    class Docs(discord.SlashCommand):
        ...

    class Python(discord.SlashCommand, parent=Docs):
        ...

    class Dpy(discord.SlashCommand, parent=Python, group=True):
        ...

.. code-block:: text

    docs
    |
    |__ python
        |
        |__ dpy <-- a subcommand cannot contain a subcommand group

An example of a valid subcommand group structure:

.. code-block:: python3

    class Permissions(discord.SlashCommand):
        ...

    class User(discord.SlashCommand, parent=Permissions, group=True):
        ...

    class Get(discord.SlashCommand, parent=User):
        ...

    class Edit(discord.SlashCommand, parent=User):
        ...

.. code-block:: text

    permissions
    |
    |__ user
        |
        |__ get
        |
        |__ edit

An example of an invalid subcommand group structure:

.. code-block:: python3

    class Permissions(discord.SlashCommand):
        ...

    class User(discord.SlashCommand, parent=Permissions, group=True):
        ...

    class Get(discord.SlashCommand, parent=User, group=True):
        ...

.. code-block:: text

    permissions
    |
    |__ user
        |
        |__ get <-- a subcommand group cannot contain a subcommand group

Autocomplete
------------

Only options of type ``str``, ``int``, or ``float`` can be autocomplete options.
To declare an autocomplete option, decorate a method with ``option.autocomplete``. The method can be either of the following:

* A coroutine function that returns an iterable of ``ApplicationCommandOptionChoice`` objects or strings.
* An async generator that yields ``ApplicationCommandOptionChoice`` objects or strings.

Strings are interpreted as the name AND value for the choice.

Autocomplete option callbacks receive one argument: the response from a user typing the option; a ``discord.AutocompleteResponse`` object.

``discord.AutocompleteResponse``
--------------------------------

* interaction: ``discord.Interaction`` - The interaction of the response.
* value: ``str`` - The data the user is typing.
* command: ``discord.SlashCommand`` - The slash command used.
* options: ``discord.ApplicationCommandOptions`` - The options of the slash command used. Note that not all objects may be resolved:

  * Without the member intents, user and mentionable (if a user was mentioned) options will be ``discord.Object`` objects.
  * Without the guild intent, user and mentionable (if a role was mentioned) options will be ``discord.Object`` objects.
  * Without the guild intent, channel options will be ``discord.PartialMessageable`` objects.
  * If the bot does not have access the role, user, or channel, even if it has the relevant intents, the objects will **not** be resolved.

Quick example:

.. code-block python3

    FRUITS = [
        'Apple',
        'Pear',
        'Banana',
        ...
    ]

    class Fruit(discord.SlashCommand):
        # we set the type kwarg instead of typehinting to avoid type checker errors
        # when using the `autocomplete` decorator
        fruit = discord.application_command_option(description='The fruit to choose', type=str)

        # this function must be async and can also return an iterable of strings, integers or floats
        @fruit.autocomplete
        async def fruit_autocomplete(self, response: discord.AutocompleteResponse) -> typing.AsyncIterator[str]:
            for fruit in FRUITS:
                if response.value.lower() in fruit.lower():
                    yield fruit

Message Commands
----------------

* ``discord.MessageCommandResponse``

  * interaction: ``discord.Interaction`` - The interaction of the response.
  * target: ``discord.Message`` - The message the command was used on.
  * command: ``discord.MessageCommand`` - The message command used.

User Commands
-------------

* ``discord.UserCommandResponse``

  * interaction: ``discord.Interaction`` - The interaction of the response
  * target: ``Union[discord.User, discord.Member]`` - The user or member the command was used on.
  * command: ``discord.MessageCommand`` - The user command used.

``Client``
----------
Keyword arguments to the constructor:

* register_application_commands_at_startup: ``bool``

  * Whether ``Client.register_application_commands`` should be called in ``Client.login``. It is recommended to set this to ``False`` when the application commands added to the client are the same (having the exact same name and options) as the previous time they were added. Defaults to ``True``.

    .. note::
        If this is set to ``True``, ``Client.register_application_commands`` will be created as a task, which means that the bot may connect to the gateway before all application commands are registered. ``on_ready`` and ``wait_until_ready`` will be delayed to wait for ``Client.register_application_commands`` to finish, regardless of whether an error was raised in it or not.

Methods:

* ``add_application_command(application_command)``

  * Adds an application command to the client.

    **Parameters**

    * application_command: ``Union[SlashCommand, MessageCommand, UserCommand]`` - The application command to add.

    **Raises**

    * ``TypeError`` - The application command passed is not an application command instance.
* ``remove_application_command(application_command)``

  * Removes an application command from the client.

    **Parameters**

    * application_command: ``Union[SlashCommand, MessageCommand, UserCommand, Type[Union[SlashCommand, MessageCommand, UserCommand]]]`` - The application command to remove. This can be an instance of the application command or its class.

    **Raises**

    * ``TypeError`` - The application command passed is not an application command.

    **Returns**

    ``Optional[Union[SlashCommand, MessageCommand, UserCommand]]`` - The application command that was removed. ``None`` if not found.
* ``add_application_command_check(func)``

  * Adds a global application command check to the client.

    This is the non-decorator interface to ``Client.application_command_check``.

    **Parameters**

    * func - The function that was used as a global check. This function can either be a regular function or a coroutine.
* ``@application_command_check``

  * A decorator that adds a global application command check to the client.

    A global check is similar to an application command's ``command_check`` method
    that is applied on a per command basis except it is run before any command checks
    have been run and applies to every application command the client has.

    .. note::

        This function can either be a regular function or a coroutine.

    Similar to an application command's ``command_check``, this takes a single parameter, which is the response of the application command. The type of it can be
    ``SlashCommandResponse``, ``MessageCommandResponse`` or ``UserCommandResponse``.

    Quick example:

    .. code-block:: python3

        @client.application_command_check
        async def check_commands(response):
            return await client.is_owner(response.user)
* ``@application_command``

  * A decorator that adds an application command to the client.

    The class being decorated must subclass ``SlashCommand``, ``MessageCommand`` or ``UserCommand``.

    This decorator is a shortcut method to ``Client.add_application_command`` that passes an instantiated version
    of the decorated class.

    .. note::

        If you need to pass parameters to the ``__init__`` of the class,
        call ``Client.add_application_command`` yourself.

    **Raises**

    * ``TypeError`` - The application command passed does not derive from a valid application command class.
* ``await register_application_commands()``

  * Registers all application commands added to the client. This will be called in ``Client.login`` if
    ``Client.register_application_commands_at_startup`` is ``True``.

    .. note::
        This overwrites existing application commands. For example, if an existing
        slash command has the same name as the one you are registering, it will be
        overwritten.

    .. note::
        Global commands may take 1 hour to register in all guilds.

    **Raises**

    * ``discord.HTTPException`` - Registering the application commands failed.

Properties:

* application_commands: ``List[Union[SlashCommand, MessageCommand, UserCommand]]`` - A list of application commands added to the client.

``Cog``
-------
* ``add_application_command(application_command)``

  * TODO

* ``remove_application_command(application_command)``

  * TODO

* ``get_application_commands()``

  * TODO

* ``cog_application_command_check(response)``

  * Similar to the ``cog_command_check`` method, this method is ran for application commands added to this cog. It receives one argument: the response of the command used. This method *could be a coroutine*.
