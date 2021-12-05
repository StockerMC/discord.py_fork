Application Commands
====================

Application commands are based on the class based implementation of the `slash command DSL <https://gist.github.com/Rapptz/2a7a299aa075427357e9b8a970747c2c>`_ Rapptz made.

Examples of application commands can be found in the `examples/application_commands <https://github.com/StockerMC/discord.py/tree/master/examples/application_commands>`_ directory.

There are three classes you can derive from for making application commands. Keyword arguments are passed to them through the class declaration instead of through the ``__init__`` of the class.
The classes and the keyword arguments each of them take are as follows:

* ``discord.SlashCommand``

  * name: ``str`` - The name of the slash command. This defaults to the name of the class.
  * description: ``str`` - The description of the slash command. This is required.
  * guild_ids: ``Optional[List[int]]`` - The IDs of the guilds to upload the slash command to. It is recommended to set this while testing to speed up the registering of the command. Defaults to ``None``.
  * global_command: ``bool`` - Whether the slash command is a global command. Defaults to ``True``.
  * parent: ``SlashCommand`` - See <Slash Command Groups link>
  * group: ``bool``- See <Slash Command Groups link>
  * default_permission: ``bool`` - Whether the slash command is enabled by default when the application is added to a guild. Defaults to ``True``.
* ``discord.MessageCommand``

  * name: ``str`` - The name of the message command. This defaults to the name of the class.
* ``discord.UserCommand``

  * name: ``str`` - The name of the user command. This defaults to the name of the class.

``Client``
----------
Keyword arguments to the constructor:

* register_application_commands_at_startup: ``bool``

  * Whether ``Client.register_application_commands`` should be called in ``Client.login``. It is recommended to set this to ``False`` when the application commands added to the client are the same (having the exact same name and options) as the previous time they were added. Defaults to ``True``.

    .. note::
        If this is set to ``True``, ``Client.register_application_commands`` will be created as a task, which means that the bot may connect to the gateway before all application commands are registered. ``on_ready`` and ``wait_until_ready`` will be delayed to wait for ``Client.register_application_commands`` to finish, regardless of whether an error was raised in it or not.

Methods:

* add_application_command

  * Adds an application command to the client.

    **Parameters**

    * application_command: ``Union[SlashCommand, MessageCommand, UserCommand]`` - The application command to add.

    **Raises**

    * ``TypeError`` - The application command passed is not an application command instance.
* remove_application_command

  * Removes an application command from the client.

    **Parameters**

    * application_command: ``Union[SlashCommand, MessageCommand, UserCommand, Type[Union[SlashCommand, MessageCommand, UserCommand]]]`` - The application command to remove. This can be an instance of the application command or its class.

    **Raises**

    * ``TypeError`` - The application command passed is not an application command.

    **Returns**

    ``Optional[Union[SlashCommand, MessageCommand, UserCommand]]`` - The application command that was removed. ``None`` if not found.
* add_application_command_check

  * Adds a global application command check to the client.

    This is the non-decorator interface to ``Client.application_command_check``.

    **Parameters**

    * func - The function that was used as a global check. This function can either be a regular function or a coroutine.
* application_command_check

  * A decorator that adds a global application command check to the client.

    A global check is similar to an application command's ``command_check`` method
    that is applied on a per command basis except it is run before any command checks
    have been run and applies to every application command the client has.

    .. note::

        This function can either be a regular function or a coroutine.

    This takes a single parameter, which is the response of the application command. The type of it can be
    ``SlashCommandResponse``, ``MessageCommandResponse`` or ``UserCommandResponse``.

    Example:

    .. code-block:: python3

        @client.application_command_check
        async def check_commands(response):
            return await client.is_owner(response.user)
* application_command

  * A decorator that adds an application command to the client.

    The class being decorated must subclass ``SlashCommand``, ``MessageCommand`` or ``UserCommand``.

    This decorator is a shortcut method to ``Client.add_application_command`` that passes an instantiated version
    of the decorated class.

    .. note::

        If you need to pass parameters to the ``__init__`` of the class,
        call ``Client.add_application_command`` yourself.

    **Raises**

    * ``TypeError`` - The application command passed does not derive from a valid application command class.
* register_application_commands: `Coroutine function <https://docs.python.org/3/library/asyncio-task.html#coroutine>`_

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


Slash Command Groups
--------------------
...
