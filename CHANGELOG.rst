Change Log
==========

- Fully typehinted the library

September 10, 2021
^^^^^^^^^^^^^^^^^^

Implemented welcome screens.

September 21, 2021
^^^^^^^^^^^^^^^^^^

Implemented application commands:
    - Based on `Danny's class based slash command DSL <https://gist.github.com/Rapptz/2a7a299aa075427357e9b8a970747c2c>`_
    ******* - Slash command autocompletion
    - `Examples <https://gist.github.com/StockerMC/discord.py/examples/application_commands>`_
    - Documentation: TODO

September 24, 2021
^^^^^^^^^^^^^^^^^^

Added cogs, extensions and listeners to ``Client``:
    - Moved ``Cog`` and ``CogMeta`` into the discord namespace.
    - Application commands can be added to cogs
    - For backwards compatibility, ``Cog`` and ``CogMeta`` are imported into the ``ext.commands`` namespace as well.

September 28, 2021
^^^^^^^^^^^^^^^^^^

Implemented role icons.

October 8, 2021
^^^^^^^^^^^^^^^

Implemented autocompletion support for slash command options.

December 20, 2021
^^^^^^^^^^^^^^^^^

- Implemented member timeouts.
- Implemented guild scheduled events.
