"""
discord.ext.commands
~~~~~~~~~~~~~~~~~~~~~

An extension module to facilitate creation of bot commands.

:copyright: (c) 2015-present Rapptz
:license: MIT, see LICENSE for more details.
"""

from .bot import *
from .context import *
from .core import *
from .errors import *
from .help import *
from .converter import *
from .cooldowns import *
from .flags import *
from discord.cog import (
    Cog as Cog,
    CogMeta as CogMeta,
)
