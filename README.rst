discord.py
==========

.. image:: https://discord.com/api/guilds/888552315848622100/embed.png
   :target: https://discord.gg/tEbbhbuvP8
   :alt: Discord server invite

Version: 2.1.0

Minimum python version: 3.8

A modern, easy to use, feature-rich, and async ready API wrapper for Discord written in Python.

This is a fork of discord.py
--------------------------

Please read the `gist <https://gist.github.com/Rapptz/4a2f62751b9600a31a0d3c78100287f1>`_ for why the original was discontinued.

A list of changes made to the fork from the original are in the `changelog <CHANGELOG.rst>`_.

Application commands are documented in `<application_commands.md>`_.

This fork is not being worked on anymore
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In light of discord.py `resuming development <https://gist.github.com/Rapptz/c4324f17a80c94776832430007ad40e6>`_, this fork will not be worked on anymore.


Key Features
-------------

- Modern Pythonic API using ``async`` and ``await``.
- Proper rate limit handling.
- Optimised in both speed and memory.

Installing
----------

**Python 3.8 or higher is required**

To install the library without full voice support, you can just run the following command:

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U git+https://github.com/StockerMC/discord.py_fork

    # Windows
    py -3 -m pip install -U git+https://github.com/StockerMC/discord.py_fork

Otherwise to get voice support you should run the following command:

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U "git+https://github.com/StockerMC/discord.py_fork[voice]"

    # Windows
    py -3 -m pip install -U git+https://github.com/StockerMC/discord.py_fork[voice]


To install the development version, do the following:

.. code:: sh

    $ git clone git+https://github.com/StockerMC/discord.py_fork
    $ cd discord.py
    $ python3 -m pip install -U .[voice]


Optional Packages
~~~~~~~~~~~~~~~~~~

* `PyNaCl <https://pypi.org/project/PyNaCl/>`__ (for voice support)

Please note that on Linux installing voice you must install the following packages via your favourite package manager (e.g. ``apt``, ``dnf``, etc) before running the above commands:

* libffi-dev (or ``libffi-devel`` on some systems)
* python-dev (e.g. ``python3.6-dev`` for Python 3.6)

Quick Example
--------------

.. code:: py

    import discord

    class MyClient(discord.Client):
        async def on_ready(self):
            print(f'Logged in as {self.user} (ID: {self.user.id})')
            print('------')

        async def on_message(self, message: discord.Message):
            # don't respond to ourselves
            if message.author == self.user:
                return

            if message.content == 'ping':
                await message.channel.send('pong')

    client = MyClient()
    client.run('token')

Bot Example
~~~~~~~~~~~~~

.. code:: py

    import discord
    from discord.ext import commands

    bot = commands.Bot(command_prefix='>')

    @bot.command()
    async def ping(ctx: commands.Context):
        await ctx.send('pong')

    bot.run('token')

Slash Command Example
~~~~~~~~~~~~~

.. code:: py

    import discord

    class MyClient(discord.Client):
        async def on_ready(self):
            print(f'Logged in as {self.user} (ID: {self.user.id})')
            print('------')

    client = MyClient()

    # setting `guild_ids` in development is better when possible because
    # registering global commands has a 1 hour delay
    @client.application_command
    class Avatar(discord.SlashCommand, guild_ids=[123]):
        """Get information about yourself or the provided user."""

        # the `required` kwarg keyword argument can also be set to `False`
        # instead of typehinting the argument as optional
        user: typing.Optional[discord.User] = discord.application_command_option(
            description='The user to get information about.',
            # the default callback can also be a coroutine function
            default=lambda response: response.user,
        )

        async def callback(self, response: discord.SlashCommandResponse):
            avatar = response.options.user.display_avatar.url
            await response.interaction.response.send_message(avatar, ephemeral=True)

    client.run('token')

You can find more examples in the examples directory.

Links
------

- `Official Discord Server <https://discord.gg/tEbbhbuvP8>`_
