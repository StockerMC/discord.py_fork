Change Log
==========

- Fully typed the library.

September 10, 2021
------------------

Implemented welcome screens:

- Added the ``discord.WelcomeScreen`` and ``discord.WelcomeScreenChannel`` classes.
- Added the ``discord.Guild.welcome_screen`` and ``discord.Guild.edit_welcome_screen`` methods.

Application Commands
--------------------

September 21, 2021
^^^^^^^^^^^^^^^^^^

Implemented application commands:

- Based on `Danny's class based slash command DSL <https://gist.github.com/Rapptz/2a7a299aa075427357e9b8a970747c2c>`_
- `Examples <https://gist.github.com/StockerMC/discord.py/examples/application_commands>`_
- Documentation: TODO

October 8, 2021
^^^^^^^^^^^^^^^

Implemented autocompletion support for slash command options.

September 24, 2021
------------------

Added cogs, extensions and listeners to ``Client``:

- Moved ``Cog`` and ``CogMeta`` into the discord namespace.
- Application commands can be added to cogs
- For backwards compatibility, ``Cog`` and ``CogMeta`` are imported into the ``ext.commands`` namespace as well.

September 28, 2021
------------------

Implemented role icons:

- Added the ``discord.Role.icon`` property.
- Added the ``discord.Member.role_icon`` property.

Member Timeouts
---------------

December 20, 2021
^^^^^^^^^^^^^^^^^

Implemented member timeouts:

- Added the ``Member.timeout_until`` attribute.
- Added the ``timeout_until`` keyword argument to ``Member.edit``.

December 25, 2021
^^^^^^^^^^^^^^^^^

Renamed all occurrences of ``timeout_until`` to ``timed_out_until``.

December 21, 2021
^^^^^^^^^^^^^^^^^

- Added the ``Member.timed_out`` property.

Guild Scheduled Events
----------------------

December 20, 2021
^^^^^^^^^^^^^^^^^

Implemented guild scheduled events:

- Added the ``discord.ScheduledEvent`` class.
- Added the ``discord.Guild.create_scheduled_event`` method.
- Added the following events:

  - ``on_guild_scheduled_event_create``
  - ``on_guild_scheduled_event_delete``
  - ``on_guild_scheduled_event_update``
  - ``on_guild_scheduled_event_user_add``
  - ``on_raw_guild_scheduled_event_user_add``
  - ``on_guild_scheduled_event_user_remove``
  - ``on_raw_guild_scheduled_event_user_remove``

December 22, 2021
-----------------

Added the ``file`` and ``files`` keyword arguments to ``Message.edit`` for editing/adding files to a message.

January 16, 2022
----------------

Added the ``Interaction.locale`` and ``Interaction.guild_locale`` attributes

January 18, 2022
----------------

Allow guild banner assets to be animated.

Suppress Embeds When Sending Messages
-------------------------------------

Added the ability to suppress embeds when sending messages:

January 22, 2022
^^^^^^^^^^^^^^^^

Added the ``suppress`` parameter to ``abc.Messageable.send`` and ``InteractionResponse.send_message``

January 25, 2022
^^^^^^^^^^^^^^^^

Added the ``suppress`` parameter to ``Webhook.send`` and ``SyncWebhook.send``

January 23, 2022
----------------

Added ``Thread.created_at``.

January 25, 2022
----------------

- Added ``ScheduledEvent.cover``.
- Added missing parameters to interaction methods

  * ``Interaction.edit_original_message``
  
    * ``attachments``
  
  * ``InteractionResponse.edit_message``
  
    * ``file``
    * ``files``
    * ``allowed_mentions``
  
  * ``InteractionMessage.edit``
  
    * ``attachments``

February 13, 2022
-----------------

- Added the ``spammer`` user flag
- Changed ``Guild.mfa_level`` to the newly added ``MFALevel`` enum
- Added the ``str(x)`` method to the ``Locale`` enum

February 14, 2022
-----------------

- Added the ``slowmode_delay`` keyword argument to ``TextChannel.create_thread`` and ``Message.create_thread``
- Added the ``reason`` keyword argument to ``Message.create_thread``
