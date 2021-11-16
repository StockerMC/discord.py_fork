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

import datetime
from typing import TYPE_CHECKING, Optional, Union, List

from .mixins import Hashable
from .abc import Snowflake
from .utils import MISSING, _get_as_snowflake, snowflake_time, parse_time
from .user import User
from .member import Member
from .enums import (
    ScheduledEventPrivacyLevel,
    ScheduledEventEntityType,
    ScheduledEventStatus,
    try_enum,
)

if TYPE_CHECKING:
    from .types.scheduled_events import (
        ScheduledEvent as ScheduledEventPayload,
        EditScheduledEvent as EditScheduledEventPayload,
        ScheduledEventMetaData,
    )

    from .state import ConnectionState
    from .guild import Guild
    from .channel import StageChannel, VoiceChannel


__all__ = (
    'ScheduledEvent',
)

class ScheduledEvent(Hashable):
    """Represents a Discord scheduled event of a :class:`Guild`.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The ID of the scheduled event.
    guild_id: :class:`int`
        The ID of the guild the scheduled event belongs to
    channel_id: Optional[:class:`int`]
        The ID of the channel in which the scheduled event will be hosted If :attr:`.entity_type` is
        :attr:`ScheduledEventEntityType.external` or :attr:`ScheduledEventEntityType.none`, this will be ``None``.
    creator_id: :class:`int`
        The ID of the user that created the scheduled event.
    name: :class:`str`
        The name of the scheduled event.
    scheduled_start_time: :class:`datetime.datetime`
        The time the scheduled event will start in UTC.
    scheduled_end_time: Optional[:class:`datetime.datetime`]
        The time the scheduled event will end in UTC, if it has a scheduled time to end.
    privacy_level: :class:`ScheduledEventPrivacyLevel`
        The privacy level of the scheduled event.
    status: :class:`ScheduledEventStatus`
        The status of the scheduled event.
    entity_type: :class:`ScheduledEventEntityType`
        The type of hosting entity associated with the scheduled event.
    entity_id: :class:`int`
        The ID of the hosting entity associated with the scheduled event.
    speaker_ids: List[:class:`int`]
        The IDs of users speaking in the stage channel.
    location: Optional[:class:`str`]
        The location of the scheduled event, if :attr:`.entity_type` is :attr:`ScheduledEventEntityType.external`.
    subscribed_user_ids: List[:class:`int`]
        The IDs of users subscribed to the scheduled event.

        .. note::

            This is only modified when discord sends the corresponding events (``guild_scheduled_event_user_add``
            and ``guild_scheduled_event_user_remove``). This means that the returned list may be incomplete, and it
            will be empty if the scheduled event wasn't returned by :attr:`Guild.get_scheduled_event`.
    user_count: Optional[:class:`int`]
        The number of users subscribed to the scheduled event. This is only provided if
        the scheduled event was fetched with :meth:`Guild.fetch_scheduled_events` with the
        ``with_user_counts`` parameter set to ``True``.
    """

    __slots__ = (
        'id',
        'guild_id',
        'channel_id',
        'creator_id',
        'name',
        'scheduled_start_time',
        'scheduled_end_time',
        'privacy_level',
        'status',
        'entity_type',
        'entity_id',
        'speaker_ids',
        'location',
        'subscribed_user_ids',
        'subscribed_users',
        'user_count',
        '_creator',
        '_image',
        '_state',
    )

    def __init__(self, *, data: ScheduledEventPayload, state: ConnectionState) -> None:
        self.subscribed_user_ids: List[int] = []
        self._state: ConnectionState = state
        self._update(data)

    def _update(self, data: ScheduledEventPayload) -> None:
        self.id: int = int(data['id'])
        self.guild_id: int = int(data['guild_id'])
        self.channel_id: Optional[int] = _get_as_snowflake(data, 'channel_id')
        self.scheduled_start_time: datetime.datetime = parse_time(data['scheduled_start_time'])
        self.scheduled_end_time: Optional[datetime.datetime] = parse_time(data['scheduled_end_time'])
        self.privacy_level: ScheduledEventPrivacyLevel = try_enum(ScheduledEventPrivacyLevel, data['privacy_level'])
        self.status: ScheduledEventStatus = try_enum(ScheduledEventStatus, data['status'])
        self.entity_type: ScheduledEventEntityType = try_enum(ScheduledEventEntityType, data['entity_type'])
        self.entity_id: Optional[int] = _get_as_snowflake(data, 'entity_id')
        self.user_count: Optional[int] = _get_as_snowflake(data, 'user_count')

        self._creator: Optional[User] = None
        self.creator_id: Optional[int] = None
        try:
            creator_data = data['creator']
            self._creator = User(state=self._state, data=creator_data)
            self.creator_id = _get_as_snowflake(creator_data, 'channel_id')
        except KeyError:
            pass

        self.speaker_ids: List[int] = []
        self.location: Optional[str] = None
        entity_metadata = data['entity_metadata']
        if entity_metadata is not None:
            self.speaker_ids = [int(speaker_id) for speaker_id in entity_metadata.get('speaker_ids', [])]
            self.location = entity_metadata.get('location')

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: The scheduled event's creation time in UTC."""
        return snowflake_time(self.id)

    @property
    def guild(self) -> Guild:
        """:class:`Guild`: The guild this emoji belongs to."""
        # the guild won't be None here
        return self._state._get_guild(self.guild_id)  # type: ignore

    @property
    def channel(self) -> Optional[Union[StageChannel, VoiceChannel]]:
        """Union[:class:`StageChannel`, :class:`VoiceChannel`]: The channel in which the scheduled event will be hosted
        If :attr:`.entity_type` is :attr:`ScheduledEventEntityType.external` or :attr:`ScheduledEventEntityType.none`,
        this will be ``None``.
        """
        # the returned channel type will be correct
        return self._state.get_channel(self.channel_id)  # type: ignore

    @property
    def creator(self) -> Optional[Union[User, Member]]:
        """Optional[Union[:class:`User`, :class:`Member`]]: The user or member that created the scheduled event."""
        return (self.creator_id is not None and self.guild.get_member(self.creator_id)) or self._creator 

    @property
    def speakers(self) -> List[Member]:
        """List[:class:`Member`]: Returns all speakers of the stage channel."""
        ret = []
        for speaker_id in self.speaker_ids:
            member = self.guild.get_member(speaker_id)
            if member is not None:
                ret.append(member)
        return ret

    @property
    def subscribed_users(self) -> List[Member]:
        """List[:class:`Member`]: Returns users subscribed to the stage channel.
        
        .. note::

            This is only modified when discord sends the corresponding events (``guild_scheduled_event_user_add``
            and ``guild_scheduled_event_user_remove``). This means that the returned list may be incomplete, and it
            will be empty if the scheduled event wasn't returned by :attr:`Guild.get_scheduled_event`.
        """
        ret = []
        for subscribed_user_id in self.subscribed_user_ids:
            member = self.guild.get_member(subscribed_user_id)
            if member is not None:
                ret.append(member)
        return ret

    async def edit(
        self,
        channel: Optional[Snowflake] = MISSING,
        speakers: List[Snowflake] = MISSING,
        location: str = MISSING,
        name: str = MISSING,
        privacy_level: ScheduledEventPrivacyLevel = MISSING,
        scheduled_start_time: datetime.datetime = MISSING,
        scheduled_end_time: datetime.datetime = MISSING,
        description: str = MISSING,
        entity_type: ScheduledEventEntityType = MISSING,
        status: ScheduledEventStatus = MISSING,
    ) -> ScheduledEvent:
        """|coro|
        
        Edits the scheduled event.

        You must have the :attr:`~Permissions.manage_events` permission
        to edit the scheduled event.

        Parameters
        ---------
        channel: Optional[:class:`abc.Snowflake`]
            The channel of the scheduled event. This is required if :attr:`.entity_type` is
            :attr:`ScheduledEventEntityType.stage_instance` or :attr:`ScheduledEventEntityType.voice`.
        speakers: List[:class:`abc.Snowflake`]
            The speakers of the stage channel.
        location: :class:`str`
            The location of the scheduled event.
        name: :class:`str`
            The name of the scheduled event.
        privacy_level: :class:`ScheduledEventPrivacyLevel`
            The privacy level of the scheduled event.
        scheduled_start_time: :class:`datetime.datetime`
            The time to schedule the scheduled event.
        scheduled_end_time: :class:`datetime.datetime`
            The time when the scheduled event is scheduled to end.
        entity_type: :class:`ScheduledEventEntityType`
            The entity type of the scheduled event.
        status: :class:`ScheduledEventStatus`
            The status of the scheduled event.
        """

        payload: EditScheduledEventPayload = {}
        entity_metadata: ScheduledEventMetaData = {}

        if speakers is not MISSING:
            entity_metadata['speaker_ids'] = [speaker.id for speaker in speakers]

        if location is not MISSING:
            entity_metadata['location'] = location

        if channel is not MISSING:
            if channel is None:
                payload['channel_id'] = None
            else:
                payload['channel_id'] = channel.id

        if name is not MISSING:
            payload['name'] = name

        if privacy_level is not MISSING:
            payload['privacy_level'] = privacy_level.value

        if scheduled_start_time is not MISSING:
            if scheduled_start_time.tzinfo:
                payload['scheduled_start_time'] = scheduled_start_time.astimezone(tz=datetime.timezone.utc).isoformat()
            else:
                payload['scheduled_start_time'] = scheduled_start_time.replace(tzinfo=datetime.timezone.utc).isoformat()

        if scheduled_end_time is not MISSING:
            if scheduled_end_time.tzinfo:
                payload['scheduled_end_time'] = scheduled_end_time.astimezone(tz=datetime.timezone.utc).isoformat()
            else:
                payload['scheduled_end_time'] = scheduled_end_time.replace(tzinfo=datetime.timezone.utc).isoformat()

        if description is not MISSING:
            payload['description'] = description

        if entity_type is not MISSING:
            payload['entity_type'] = entity_type.value

        if status is not MISSING:
            payload['entity_type'] = status.value

        if entity_metadata:
            payload['entity_metadata'] = entity_metadata

        data = await self._state.http.edit_scheduled_event(self.guild_id, self.id, payload)
        return self.__class__(state=self._state, data=data)
