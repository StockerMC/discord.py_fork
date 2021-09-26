# This is merely a tag type to avoid circular import issues.
# Yes, this is a terrible solution but ultimately it is the only solution.
# This was moved out of the ext.commands namespace so discord.Cog/CogMeta
# could be imported into it for backwards compatibility.
class _BaseCommand:
    __slots__ = ()
