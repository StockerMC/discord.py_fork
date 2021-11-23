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
from typing import TYPE_CHECKING, Optional, Union

from .mixins import Hashable
from .errors import ClientException
from .utils import MISSING, _get_as_snowflake, snowflake_time, parse_time
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

    from .abc import Snowflake
    from .member import Member
    from .user import User
    from .state import ConnectionState
    from .guild import Guild
    from .channel import StageChannel, VoiceChannel
    from .iterators import ScheduledEventUserIterator


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
        The ID of the guild the scheduled event belongs to.
    channel_id: Optional[:class:`int`]
        The ID of the channel in which the scheduled event will be hosted If :attr:`.entity_type` is
        :attr:`ScheduledEventEntityType.external` or :attr:`ScheduledEventEntityType.none`, this will be ``None``.
    creator_id: Optional[:class:`int`]
        The ID of the user that created the scheduled event.
    name: :class:`str`
        The name of the scheduled event.
    description: Optional[:class:`str`]
        The description of the scheduled event.
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
    location: Optional[:class:`str`]
        The location of the scheduled event, if :attr:`.entity_type` is :attr:`ScheduledEventEntityType.external`.
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
        'description',
        'scheduled_start_time',
        'scheduled_end_time',
        'privacy_level',
        'status',
        'entity_type',
        'entity_id',
        'location',
        'user_count',
        '_creator',
        '_state',
    )

    def __init__(self, *, data: ScheduledEventPayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self._update(data)

    def _update(self, data: ScheduledEventPayload) -> None:
        self.id: int = int(data['id'])
        self.guild_id: int = int(data['guild_id'])
        self.channel_id: Optional[int] = _get_as_snowflake(data, 'channel_id')
        self.name: str = data['name']
        self.description: Optional[str] = data.get('description')
        self.scheduled_start_time: datetime.datetime = parse_time(data['scheduled_start_time'])
        self.scheduled_end_time: Optional[datetime.datetime] = parse_time(data['scheduled_end_time'])
        self.privacy_level: ScheduledEventPrivacyLevel = try_enum(ScheduledEventPrivacyLevel, data['privacy_level'])
        self.status: ScheduledEventStatus = try_enum(ScheduledEventStatus, data['status'])
        self.entity_type: ScheduledEventEntityType = try_enum(ScheduledEventEntityType, data['entity_type'])
        self.entity_id: Optional[int] = _get_as_snowflake(data, 'entity_id')
        self.user_count: Optional[int] = _get_as_snowflake(data, 'user_count')

        self.creator_id: Optional[int] = _get_as_snowflake(data, 'creator_id')
        self._creator: Optional[User] = None
        try:
            # circular import
            from .user import User

            creator_data = data['creator']
            self._creator = User(state=self._state, data=creator_data)
        except KeyError:
            pass

        self.location: Optional[str] = None
        entity_metadata = data['entity_metadata']
        if entity_metadata is not None:
            self.location = entity_metadata.get('location')

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: The scheduled event's creation time in UTC."""
        return snowflake_time(self.id)

    @property
    def guild(self) -> Optional[Guild]:
        """:class:`Guild`: The guild the scheduled event belongs to.

        Could be ``None`` if the bot is not in the guild.
        """
        return self._state._get_guild(self.guild_id)

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
        if self.creator_id is None:
            return None

        if self.guild is None:
            return self._state.get_user(self.creator_id) or self._creator

        return self.guild.get_member(self.creator_id)

    # TODO: should with_member be removed?
    def fetch_users(
        self,
        *,
        limit: Optional[int] = 100,
        before: Optional[Snowflake] = None,
        after: Optional[Snowflake] = None,
        with_member: Optional[bool] = None
    ) -> ScheduledEventUserIterator:
        """|coro|

        Retrieves an :class:`AsyncIterator` that enables receiving users subscribed to the scheduled event.

        All parameters are optional.

        Parameters
        ------------
        limit: Optional[:class:`int`]
            The maximum number of users to retrieve. Defaults to 100.
            Pass ``None`` to fetch all users. Note that this is potentially slow.
            reacted to the message.
        before: Optional[Union[:class:`.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve members before this date or object.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        after: Optional[Union[:class:`.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve users after this date or object.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        with_member: Optional[:class:`bool`]
            Whether to fetch the users with member data. If this is ``False`` and
            :attr:`Intents.members` is disabled, members subscribed to the event
            will be of type :class:`User`. Defaults to ``True``

        Raises
        -------
        ClientException
            The guild was not cached and returned ``None``.
        HTTPException
            Getting the users failed.

        Yields
        ------
        Union[:class:`Member`, :class:`User`]
            The member (if retrievable) or user subscribed to the scheduled event.
            If you have :attr:`Intents.members` and the member is in the scheduled event's guild,
            it will be a :class:`Member`. Otherwise, it will be a :class:`User`.

        Examples
        --------

        Usage ::

            async for user in scheduled_event.fetch_users(limit=10):
                print(user.name)

        Flattening into a list ::

            users = await scheduled_event.fetch_users(limit=10).flatten()
            # users is now a list of User/Member...
        """

        from .iterators import ScheduledEventUserIterator  # circular import

        if self.guild is None:
            raise ClientException('Guild not found.')

        if limit is None and self.user_count is not None:
            limit = self.user_count

        if with_member is None:
            with_member = True

        return ScheduledEventUserIterator(
            self.id,
            guild=self.guild,
            limit=limit,
            after=after,
            before=before,
            with_member=with_member,
        )

    async def edit(
        self,
        channel: Optional[Snowflake] = MISSING,
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

    async def delete(self) -> None:
        """|coro|
        
        Delete's the scheduled event.

        You must have the :attr:`~Permissions.manage_events` permission to
        use this.

        Raises
        --------
        Forbidden
            You do not have permissions to delete the scheduled event.
        HTTPException
            Deleting the scheduled event failed.
        """

        await self._state.http.delete_scheduled_event(self.guild_id, self.id)
