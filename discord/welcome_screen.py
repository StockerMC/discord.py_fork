"""
The MIT License (MIT)

Copyright (c) StockerMC

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List, TypeVar, Type, Union

from .utils import MISSING
from .partial_emoji import PartialEmoji

if TYPE_CHECKING:
    from .state import ConnectionState
    from .channel import TextChannel
    from .guild import Guild
    from .invite import PartialInviteGuild
    from .object import Object

    from .types.welcome_screen import (
        WelcomeScreen as WelcomeScreenPayload,
        WelcomeScreenChannel as WelcomeScreenChannelPayload,
        EditWelcomeScreen as EditWelcomeScreenPayload,
    )

    WCT = TypeVar('WCT', bound='WelcomeScreenChannel')


__all__ = (
    'WelcomeScreen',
    'WelcomeScreenChannel',
)


class WelcomeScreen:
    """Represents a Discord welcome screen.

    Attributes
    ------------
    description: :class:`str`
        The server description shown in the welcome screen.
    welcome_channels: List[:class:`WelcomeScreenChannel`]
        The channels shown in the welcome screen.
    enabled: :class:`bool`
        Whether the welcome screen is enabled. If this is ``False``,
        the welcome screen instance was edited with ``enabled=False``.
    guild: Union[:class:`Guild`, :class:`PartialInviteGuild`, :class:`Object`]
        The guild that the welcome screen is for.
    """

    __slots__ = (
        'description',
        'welcome_channels',
        'enabled',
        'guild',
        '_state'
    )

    def __init__(self, *, state: ConnectionState, data: WelcomeScreenPayload, guild: Union[Guild, PartialInviteGuild, Object]) -> None:
        self._state: ConnectionState = state
        self.enabled: bool = True
        self.guild: Union[Guild, PartialInviteGuild, Object] = guild
        self._update(data)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} enabled={self.enabled} description={self.description!r} welcome_channels={self.welcome_channels}>'

    def _update(self, data: WelcomeScreenPayload) -> None:
        self.description: str = data['description']
        self.welcome_channels: List[WelcomeScreenChannel] = [WelcomeScreenChannel.from_state(state=self._state, data=x) for x in data['welcome_channels']]

    async def edit(
        self,
        *,
        reason: Optional[str] = None,
        enabled: Optional[bool] = MISSING,
        welcome_channels: Optional[List[WelcomeScreenChannel]] = MISSING,
        description: Optional[str] = MISSING,
    ) -> None:
        """|coro|

        Edits the welcome screen in place.

        All parameters are optional.

        Parameters
        -----------
        enabled: Optional[:class:`bool`]
            Whether to enable the welcome screen.
            If ``False``, the welcome screen will be disabled.
        welcome_channels: Optional[List[:class:`WelcomeScreenChannel`]]
            The welcome channels to edit the welcome screen with.

            .. note::

                This *replaces* the old welcome channels.
        description: Optional[:class:`str`]
            The server description shown in the welcome screen.
        reason: :class:`str`
            The reason for editing the welcome screen. Shows up on the audit log.

        Raises
        -------
        HTTPException
            Editing the welcome screen failed.
        Forbidden
            You don't have permissions to edit the welcome screen.

        Returns
        -------
        :class:`WelcomeScreen`
            The edited welcome screen.
        """
        ret: EditWelcomeScreenPayload = {}
        if enabled is not MISSING:
            ret['enabled'] = enabled

        if welcome_channels is not MISSING:
            if welcome_channels is not None:
                ret['welcome_channels'] = [channel.to_dict() for channel in welcome_channels]
            else:
                ret['welcome_channels'] = None

        if description is not MISSING:
            ret['description'] = description

        data = await self._state.http.modify_guild_welcome_screen(self.guild.id, ret, reason=reason)
        self._update(data)


class WelcomeScreenChannel:
    """Represents a Discord welcome channel.

    Attributes
    ------------
    channel_id: :class:`int`
        The channel's id
    description: :class:`str`
        The description shown for the channel.
    emoji: Optional[:class:`PartialEmoji`]
        The emoji for the channel, if one is set.
    channel: Optional[:class:`TextChannel`]
        The channel for the welcome channel.
    """

    __slots__ = (
        'channel_id',
        'description',
        'emoji',
        '_state',
    )

    def __init__(self, *, channel_id: int, description: str, emoji: Optional[PartialEmoji] = None) -> None:
        self.channel_id: int = channel_id
        # the channel will either be a TextChannel or None
        self._state: Optional[ConnectionState] = None
        self.description: str = description

        self.emoji: Optional[PartialEmoji] = emoji
        if self.emoji is not None and self._state is not None:
            self.emoji._state = self._state

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} channel_id={self.channel_id} description={self.description!r} emoji={self.emoji!r}>'

    @property
    def channel(self) -> Optional[TextChannel]:
        """Optional[:class:`TextChannel`]: Returns the welcome screen channel's TextChannel object."""
        # the returned channel will either be a TextChannel or None
        return self._state.get_channel(self.channel_id) if self._state is not None else None # type: ignore

    @classmethod
    def from_state(cls: Type[WCT], *, state: ConnectionState, data: WelcomeScreenChannelPayload) -> WCT:
        channel_id = int(data.pop('channel_id'))
        description = data.pop('description')
        emoji = PartialEmoji.from_dict(data) if data else None # type: ignore
        self = cls(channel_id=channel_id, description=description, emoji=emoji)
        self._state = state
        return self

    def to_dict(self) -> WelcomeScreenChannelPayload:
        return {
            'channel_id': self.channel_id,
            'description': self.description,
            'emoji_name': self.emoji.name if self.emoji is not None else None,
            'emoji_id': self.emoji.id if self.emoji is not None else None
        }
