Change Log
==============================

* Fully typehinted the library
* Application commands (slash commands, message commands and user commands)
    * Based on `Danny's class based slash command DSL <https://gist.github.com/Rapptz/2a7a299aa075427357e9b8a970747c2c>`_
    * Slash command autocompletion
    * `Examples <https://gist.github.com/StockerMC/discord.py/examples/application_commands>`_

* Welcome screens
* Role icons
* Added cogs and extensions to ``Client`` and moved ``Cog`` and ``CogMeta`` into the discord namespace.
    * Application commands can be added to cogs
    * Note: for backwards compatibility, ``Cog`` and ``CogMeta`` are imported into the ``ext.commands`` namespace as well.

Dec 20, 2021
^^^^^^^^^^^^

* Implemented member timeouts.
