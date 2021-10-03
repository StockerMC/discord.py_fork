"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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

import asyncio
import datetime
from typing import Awaitable, TYPE_CHECKING, TypeVar, Optional, Any, Callable, Union, List, AsyncIterator, Tuple, Dict

from .errors import NoMoreItems
from .utils import snowflake_time, time_snowflake, maybe_coroutine
from .object import Object
from .audit_logs import AuditLogEntry

__all__ = (
    'ReactionIterator',
    'HistoryIterator',
    'AuditLogIterator',
    'GuildIterator',
    'MemberIterator',
)

if TYPE_CHECKING:
    from .types.user import (
        User as UserPayload,
        PartialUser as PartialUserPayload,
    )
    from .types.audit_log import (
        AuditLog as AuditLogPayload,
        AuditLogEntry as AuditLogEntryPayload,
    )
    from .types.guild import (
        Guild as GuildPayload,
    )
    from .types.message import (
        Message as MessagePayload,
    )
    from .types.threads import (
        Thread as ThreadPayload,
        ThreadPaginationPayload,
    )
    from .types.member import MemberWithUser
    from .types.snowflake import Snowflake as _Snowflake

    from .member import Member
    from .user import User
    from .message import Message
    from .audit_logs import AuditLogEntry
    from .guild import Guild
    from .threads import Thread
    from .abc import Snowflake
    from .state import ConnectionState
    from .http import HTTPClient, Response
    from .abc import Messageable
    from .enums import AuditLogAction
    from .client import Client

T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)
OT = TypeVar('OT')
_Func = Callable[[T], Union[OT, Awaitable[OT]]]

OLDEST_OBJECT = Object(id=0)


class _AsyncIterator(AsyncIterator[T_co]):
    __slots__ = ()

    async def next(self) -> T_co:
        raise NotImplementedError

    def get(self, **attrs: Any) -> Awaitable[Optional[T_co]]:
        def predicate(elem):
            for attr, val in attrs.items():
                nested = attr.split('__')
                obj = elem
                for attribute in nested:
                    obj = getattr(obj, attribute)

                if obj != val:
                    return False
            return True

        return self.find(predicate)

    async def find(self, predicate: _Func[T_co, bool]) -> Optional[T_co]:
        while True:
            try:
                elem = await self.next()
            except NoMoreItems:
                return None

            ret = await maybe_coroutine(predicate, elem)
            if ret:
                return elem

    def chunk(self, max_size: int) -> _ChunkedAsyncIterator[T_co]:
        if max_size <= 0:
            raise ValueError('async iterator chunk sizes must be greater than 0.')
        return _ChunkedAsyncIterator(self, max_size)

    def map(self, func: _Func[T_co, OT]) -> _MappedAsyncIterator[OT]:
        return _MappedAsyncIterator(self, func)

    def filter(self, predicate: _Func[T_co, bool]) -> _FilteredAsyncIterator[T_co]:
        return _FilteredAsyncIterator(self, predicate)

    async def flatten(self) -> List[T_co]:
        return [element async for element in self]

    async def __anext__(self) -> T_co:
        try:
            return await self.next()
        except NoMoreItems:
            raise StopAsyncIteration()


def _identity(x: Any) -> Any:
    return x


class _ChunkedAsyncIterator(_AsyncIterator[List[T]]):
    def __init__(self, iterator: _AsyncIterator[T], max_size: int) -> None:
        self.iterator: _AsyncIterator[T] = iterator
        self.max_size: int = max_size

    async def next(self) -> List[T]:
        ret: List[T] = []
        n = 0
        while n < self.max_size:
            try:
                item = await self.iterator.next()
            except NoMoreItems:
                if ret:
                    return ret
                raise
            else:
                ret.append(item)
                n += 1
        return ret


class _MappedAsyncIterator(_AsyncIterator[T]):
    def __init__(self, iterator: _AsyncIterator[T], func: Callable[[T], Union[T, Awaitable[T]]]):
        self.iterator: _AsyncIterator[T] = iterator
        self.func: Callable[[T], Union[T, Awaitable[T]]] = func

    async def next(self) -> T:
        # this raises NoMoreItems and will propagate appropriately
        item = await self.iterator.next()
        return await maybe_coroutine(self.func, item)


class _FilteredAsyncIterator(_AsyncIterator[T_co]):
    def __init__(self, iterator: _AsyncIterator[T_co], predicate: _Func[T_co, bool]):
        self.iterator: _AsyncIterator[T_co] = iterator

        if predicate is None:
            predicate = _identity

        self.predicate: _Func[T_co, bool] = predicate

    async def next(self) -> T_co:
        getter = self.iterator.next
        pred = self.predicate
        while True:
            # propagate NoMoreItems similar to _MappedAsyncIterator
            item = await getter()
            ret = await maybe_coroutine(pred, item)
            if ret:
                return item


class ReactionIterator(_AsyncIterator[Union['User', 'Member']]):
    def __init__(self, message: Message, emoji: str, limit: int = 100, after: Optional[Object] = None) -> None:
        self.message: Message = message
        self.limit: int = limit
        self.after: Optional[Object] = after
        state = message._state
        self.getter: Callable[[_Snowflake, _Snowflake, str, int, Optional[_Snowflake]], Response[List[UserPayload]]] = state.http.get_reaction_users
        self.state: ConnectionState = state
        self.emoji: str = emoji
        self.guild: Optional[Guild] = message.guild
        self.channel_id: int = message.channel.id
        self.users: asyncio.Queue[Union[User, Member]] = asyncio.Queue()

    async def next(self) -> Union[User, Member]:
        if self.users.empty():
            await self.fill_users()

        try:
            return self.users.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    async def fill_users(self) -> None:
        # this is a hack because >circular imports<
        from .user import User

        if self.limit > 0:
            retrieve = self.limit if self.limit <= 100 else 100

            after = self.after.id if self.after else None
            data: List[PartialUserPayload] = await self.getter(
                self.channel_id, self.message.id, self.emoji, retrieve, after
            )

            if data:
                self.limit -= retrieve
                self.after = Object(id=int(data[-1]['id']))

            if self.guild is None or isinstance(self.guild, Object):
                for element in reversed(data):
                    await self.users.put(User(state=self.state, data=element))
            else:
                for element in reversed(data):
                    member_id = int(element['id'])
                    member = self.guild.get_member(member_id)
                    if member is not None:
                        await self.users.put(member)
                    else:
                        await self.users.put(User(state=self.state, data=element))


class HistoryIterator(_AsyncIterator['Message']):
    """Iterator for receiving a channel's message history.

    The messages endpoint has two behaviours we care about here:
    If ``before`` is specified, the messages endpoint returns the `limit`
    newest messages before ``before``, sorted with newest first. For filling over
    100 messages, update the ``before`` parameter to the oldest message received.
    Messages will be returned in order by time.
    If ``after`` is specified, it returns the ``limit`` oldest messages after
    ``after``, sorted with newest first. For filling over 100 messages, update the
    ``after`` parameter to the newest message received. If messages are not
    reversed, they will be out of order (99-0, 199-100, so on)

    A note that if both ``before`` and ``after`` are specified, ``before`` is ignored by the
    messages endpoint.

    Parameters
    -----------
    messageable: :class:`abc.Messageable`
        Messageable class to retrieve message history from.
    limit: :class:`int`
        Maximum number of messages to retrieve
    before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
        Message before which all messages must be.
    after: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
        Message after which all messages must be.
    around: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
        Message around which all messages must be. Limit max 101. Note that if
        limit is an even number, this will return at most limit+1 messages.
    oldest_first: Optional[:class:`bool`]
        If set to ``True``, return messages in oldest->newest order. Defaults to
        ``True`` if `after` is specified, otherwise ``False``.
    """

    def __init__(
        self,
        messageable: Messageable,
        limit: int,
        before: Optional[Union[Snowflake, datetime.datetime]] = None,
        after: Optional[Union[Snowflake, datetime.datetime]] = None,
        around: Optional[Union[Snowflake, datetime.datetime]] = None,
        oldest_first: Optional[bool] = None,
    ) -> None:

        if isinstance(before, datetime.datetime):
            before = Object(id=time_snowflake(before, high=False))
        if isinstance(after, datetime.datetime):
            after = Object(id=time_snowflake(after, high=True))
        if isinstance(around, datetime.datetime):
            around = Object(id=time_snowflake(around))

        if oldest_first is None:
            self.reverse: bool = after is not None
        else:
            self.reverse: bool = oldest_first

        self.messageable: Messageable = messageable
        self.limit: int = limit
        self.before: Optional[Snowflake] = before
        self.after: Optional[Snowflake] = after or OLDEST_OBJECT
        self.around: Optional[Snowflake] = around

        self._filter: Optional[Callable[[MessagePayload], bool]] = None  # message dict -> bool

        self.state: ConnectionState = self.messageable._state
        self.logs_from: Callable[..., Response[List[MessagePayload]]] = self.state.http.logs_from
        self.messages: asyncio.Queue[Message] = asyncio.Queue()

        if self.around:
            if self.limit is None:
                raise ValueError('history does not support around with limit=None')
            if self.limit > 101:
                raise ValueError("history max limit 101 when specifying around parameter")
            elif self.limit == 101:
                self.limit = 100  # Thanks discord

            self._retrieve_messages = self._retrieve_messages_around_strategy  # type: ignore
            if self.before and self.after:
                self._filter = lambda m: self.after.id < int(m['id']) < self.before.id  # type: ignore
            elif self.before:
                self._filter = lambda m: int(m['id']) < self.before.id  # type: ignore
            elif self.after:
                self._filter = lambda m: self.after.id < int(m['id'])  # type: ignore
        else:
            if self.reverse:
                self._retrieve_messages = self._retrieve_messages_after_strategy  # type: ignore
                if self.before:
                    self._filter = lambda m: int(m['id']) < self.before.id  # type: ignore
            else:
                self._retrieve_messages = self._retrieve_messages_before_strategy  # type: ignore
                if self.after and self.after != OLDEST_OBJECT:
                    self._filter = lambda m: int(m['id']) > self.after.id  # type: ignore

    async def next(self) -> Message:
        if self.messages.empty():
            await self.fill_messages()

        try:
            return self.messages.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    def _get_retrieve(self) -> bool:
        l = self.limit
        if l is None or l > 100:
            r = 100
        else:
            r = l
        self.retrieve = r
        return r > 0

    async def fill_messages(self) -> None:
        if not hasattr(self, 'channel'):
            # do the required set up
            channel = await self.messageable._get_channel()
            self.channel = channel

        if self._get_retrieve():
            data = await self._retrieve_messages(self.retrieve)
            if len(data) < 100:
                self.limit = 0  # terminate the infinite loop

            if self.reverse:
                data = reversed(data)
            if self._filter:
                data = filter(self._filter, data)

            channel = self.channel
            for element in data:
                await self.messages.put(self.state.create_message(channel=channel, data=element))

    async def _retrieve_messages(self, retrieve: int) -> List[MessagePayload]:
        """Retrieve messages and update next parameters."""
        raise NotImplementedError

    async def _retrieve_messages_before_strategy(self, retrieve: int) -> List[MessagePayload]:
        """Retrieve messages using before parameter."""
        before = self.before.id if self.before else None
        data: List[MessagePayload] = await self.logs_from(self.channel.id, retrieve, before=before)
        if len(data):
            if self.limit is not None:
                self.limit -= retrieve
            self.before = Object(id=int(data[-1]['id']))
        return data

    async def _retrieve_messages_after_strategy(self, retrieve: int) -> List[MessagePayload]:
        """Retrieve messages using after parameter."""
        after = self.after.id if self.after else None
        data: List[MessagePayload] = await self.logs_from(self.channel.id, retrieve, after=after)
        if len(data):
            if self.limit is not None:
                self.limit -= retrieve
            self.after = Object(id=int(data[0]['id']))
        return data

    async def _retrieve_messages_around_strategy(self, retrieve: int) -> List[MessagePayload]:
        """Retrieve messages using around parameter."""
        if self.around:
            around = self.around.id if self.around else None
            data: List[MessagePayload] = await self.logs_from(self.channel.id, retrieve, around=around)
            self.around = None
            return data
        return []


class AuditLogIterator(_AsyncIterator['AuditLogEntry']):
    def __init__(
        self,
        guild: Guild,
        limit: Optional[int] = None,
        before: Optional[Union[Snowflake, datetime.datetime]] = None,
        after: Optional[Union[Snowflake, datetime.datetime]] = None,
        oldest_first: Optional[bool] = None,
        user_id: Optional[int] = None,
        action_type: Optional[AuditLogAction] = None,
    ) -> None:
        if isinstance(before, datetime.datetime):
            before = Object(id=time_snowflake(before, high=False))
        if isinstance(after, datetime.datetime):
            after = Object(id=time_snowflake(after, high=True))

        if oldest_first is None:
            self.reverse: bool = after is not None
        else:
            self.reverse: bool = oldest_first

        self.guild: Guild = guild
        self.loop: asyncio.AbstractEventLoop = guild._state.loop
        self.request: Callable[..., Response[AuditLogPayload]] = guild._state.http.get_audit_logs
        self.limit: Optional[int] = limit
        self.before: Optional[Snowflake] = before
        self.user_id: Optional[int] = user_id
        self.action_type: Optional[AuditLogAction] = action_type
        self.after: Object = OLDEST_OBJECT
        self._users: Dict[int, User] = {}
        self._state: ConnectionState = guild._state

        self._filter: Optional[Callable[[AuditLogEntryPayload], bool]] = None  # entry dict -> bool

        self.entries: asyncio.Queue[AuditLogEntry] = asyncio.Queue()

        if self.reverse:
            self._strategy = self._after_strategy
            if self.before:
                self._filter = lambda m: int(m['id']) < self.before.id  # type: ignore
        else:
            self._strategy = self._before_strategy
            if self.after and self.after != OLDEST_OBJECT:
                self._filter = lambda m: int(m['id']) > self.after.id

    async def _before_strategy(self, retrieve: int) -> Tuple[List[UserPayload], List[AuditLogEntryPayload]]:
        before = self.before.id if self.before else None
        data: AuditLogPayload = await self.request(
            self.guild.id, limit=retrieve, user_id=self.user_id, action_type=self.action_type, before=before
        )

        entries = data.get('audit_log_entries', [])
        if len(data) and entries:
            if self.limit is not None:
                self.limit -= retrieve
            self.before = Object(id=int(entries[-1]['id']))
        return data.get('users', []), entries

    async def _after_strategy(self, retrieve: int) -> Tuple[List[UserPayload], List[AuditLogEntryPayload]]:
        after = self.after.id if self.after else None
        data: AuditLogPayload = await self.request(
            self.guild.id, limit=retrieve, user_id=self.user_id, action_type=self.action_type, after=after
        )
        entries = data.get('audit_log_entries', [])
        if len(data) and entries:
            if self.limit is not None:
                self.limit -= retrieve
            self.after = Object(id=int(entries[0]['id']))
        return data.get('users', []), entries

    async def next(self) -> AuditLogEntry:
        if self.entries.empty():
            await self._fill()

        try:
            return self.entries.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    def _get_retrieve(self) -> bool:
        l = self.limit
        if l is None or l > 100:
            r = 100
        else:
            r = l
        self.retrieve = r
        return r > 0

    async def _fill(self) -> None:
        from .user import User

        if self._get_retrieve():
            users, data = await self._strategy(self.retrieve)
            if len(data) < 100:
                self.limit = 0  # terminate the infinite loop

            if self.reverse:
                data = reversed(data)
            if self._filter:
                data = filter(self._filter, data)

            for user in users:
                u = User(data=user, state=self._state)
                self._users[u.id] = u

            for element in data:
                # TODO: remove this if statement later
                if element['action_type'] is None:
                    continue

                await self.entries.put(AuditLogEntry(data=element, users=self._users, guild=self.guild))


class GuildIterator(_AsyncIterator['Guild']):
    """Iterator for receiving the client's guilds.

    The guilds endpoint has the same two behaviours as described
    in :class:`HistoryIterator`:
    If ``before`` is specified, the guilds endpoint returns the ``limit``
    newest guilds before ``before``, sorted with newest first. For filling over
    100 guilds, update the ``before`` parameter to the oldest guild received.
    Guilds will be returned in order by time.
    If `after` is specified, it returns the ``limit`` oldest guilds after ``after``,
    sorted with newest first. For filling over 100 guilds, update the ``after``
    parameter to the newest guild received, If guilds are not reversed, they
    will be out of order (99-0, 199-100, so on)

    Not that if both ``before`` and ``after`` are specified, ``before`` is ignored by the
    guilds endpoint.

    Parameters
    -----------
    bot: :class:`discord.Client`
        The client to retrieve the guilds from.
    limit: :class:`int`
        Maximum number of guilds to retrieve.
    before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
        Object before which all guilds must be.
    after: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
        Object after which all guilds must be.
    """

    def __init__(
        self,
        bot: Client,
        limit: int,
        before: Optional[Union[Snowflake, datetime.datetime]] = None,
        after: Optional[Union[Snowflake, datetime.datetime]] = None,
    ):

        if isinstance(before, datetime.datetime):
            before = Object(id=time_snowflake(before, high=False))
        if isinstance(after, datetime.datetime):
            after = Object(id=time_snowflake(after, high=True))

        self.bot: Client = bot
        self.limit: int = limit
        self.before: Optional[Snowflake] = before
        self.after: Optional[Snowflake] = after

        self._filter: Optional[Callable[[GuildPayload], bool]] = None

        self.state: ConnectionState = self.bot._connection
        self.get_guilds: Callable[..., Response[List[GuildPayload]]] = self.bot.http.get_guilds
        self.guilds: asyncio.Queue[Guild] = asyncio.Queue()

        if self.before and self.after:
            self._retrieve_guilds = self._retrieve_guilds_before_strategy  # type: ignore
            self._filter = lambda m: int(m['id']) > self.after.id  # type: ignore
        elif self.after:
            self._retrieve_guilds = self._retrieve_guilds_after_strategy  # type: ignore
        else:
            self._retrieve_guilds = self._retrieve_guilds_before_strategy  # type: ignore

    async def next(self) -> Guild:
        if self.guilds.empty():
            await self.fill_guilds()

        try:
            return self.guilds.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    def _get_retrieve(self) -> bool:
        l = self.limit
        if l is None or l > 100:
            r = 100
        else:
            r = l
        self.retrieve = r
        return r > 0

    def create_guild(self, data: GuildPayload) -> Guild:
        from .guild import Guild

        return Guild(state=self.state, data=data)

    async def fill_guilds(self) -> None:
        if self._get_retrieve():
            data = await self._retrieve_guilds(self.retrieve)
            if self.limit is None or len(data) < 100:
                self.limit = 0

            if self._filter:
                data = filter(self._filter, data)

            for element in data:
                await self.guilds.put(self.create_guild(element))

    async def _retrieve_guilds(self, retrieve: int) -> List[GuildPayload]:
        """Retrieve guilds and update next parameters."""
        raise NotImplementedError

    async def _retrieve_guilds_before_strategy(self, retrieve: int) -> List[GuildPayload]:
        """Retrieve guilds using before parameter."""
        before = self.before.id if self.before else None
        data: List[GuildPayload] = await self.get_guilds(retrieve, before=before)
        if len(data):
            if self.limit is not None:
                self.limit -= retrieve
            self.before = Object(id=int(data[-1]['id']))
        return data

    async def _retrieve_guilds_after_strategy(self, retrieve: int) -> List[GuildPayload]:
        """Retrieve guilds using after parameter."""
        after = self.after.id if self.after else None
        data: List[GuildPayload] = await self.get_guilds(retrieve, after=after)
        if len(data):
            if self.limit is not None:
                self.limit -= retrieve
            self.after = Object(id=int(data[0]['id']))
        return data


class MemberIterator(_AsyncIterator['Member']):
    def __init__(self, guild: Guild, limit: int = 1000, after: Optional[Union[Snowflake, datetime.datetime]] = None) -> None:
        if isinstance(after, datetime.datetime):
            after = Object(id=time_snowflake(after, high=True))

        self.guild: Guild = guild
        self.limit: int = limit
        self.after: Snowflake = after or OLDEST_OBJECT

        self.state: ConnectionState = self.guild._state
        self.get_members: Callable[[_Snowflake, int, Optional[_Snowflake]], Response[List[MemberWithUser]]] = self.state.http.get_members
        self.members: asyncio.Queue[Member] = asyncio.Queue()

    async def next(self) -> Member:
        if self.members.empty():
            await self.fill_members()

        try:
            return self.members.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    def _get_retrieve(self) -> bool:
        l = self.limit
        if l is None or l > 1000:
            r = 1000
        else:
            r = l
        self.retrieve = r
        return r > 0

    async def fill_members(self) -> None:
        if self._get_retrieve():
            after = self.after.id if self.after else None
            data = await self.get_members(self.guild.id, self.retrieve, after)
            if not data:
                # no data, terminate
                return

            if len(data) < 1000:
                self.limit = 0  # terminate loop

            self.after = Object(id=int(data[-1]['user']['id']))

            for element in reversed(data):
                await self.members.put(self.create_member(element))

    def create_member(self, data: MemberWithUser) -> Member:
        from .member import Member

        return Member(data=data, guild=self.guild, state=self.state)


class ArchivedThreadIterator(_AsyncIterator['Thread']):
    def __init__(
        self,
        channel_id: int,
        guild: Guild,
        limit: Optional[int],
        joined: bool,
        private: bool,
        before: Optional[Union[Snowflake, datetime.datetime]] = None,
    ):
        self.channel_id: int = channel_id
        self.guild: Guild = guild
        self.limit: Optional[int] = limit
        self.joined: bool = joined
        self.private: bool = private
        self.http: HTTPClient = guild._state.http

        if joined and not private:
            raise ValueError('Cannot iterate over joined public archived threads')

        self.before: Optional[str]
        if before is None:
            self.before = None
        elif isinstance(before, datetime.datetime):
            if joined:
                self.before = str(time_snowflake(before, high=False))
            else:
                self.before = before.isoformat()
        else:
            if joined:
                self.before = str(before.id)
            else:
                self.before = snowflake_time(before.id).isoformat()

        self.update_before: Callable[[ThreadPayload], str] = self.get_archive_timestamp

        self.endpoint: Callable[..., Response[ThreadPaginationPayload]]
        if joined:
            self.endpoint = self.http.get_joined_private_archived_threads
            self.update_before = self.get_thread_id
        elif private:
            self.endpoint = self.http.get_private_archived_threads
        else:
            self.endpoint = self.http.get_public_archived_threads

        self.queue: asyncio.Queue[Thread] = asyncio.Queue()
        self.has_more: bool = True

    async def next(self) -> Thread:
        if self.queue.empty():
            await self.fill_queue()

        try:
            return self.queue.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    @staticmethod
    def get_archive_timestamp(data: ThreadPayload) -> str:
        return data['thread_metadata']['archive_timestamp']

    @staticmethod
    def get_thread_id(data: ThreadPayload) -> str:
        return data['id']  # type: ignore

    async def fill_queue(self) -> None:
        if not self.has_more:
            raise NoMoreItems()

        limit = 50 if self.limit is None else max(self.limit, 50)
        data = await self.endpoint(self.channel_id, before=self.before, limit=limit)

        # This stuff is obviously WIP because 'members' is always empty
        threads: List[ThreadPayload] = data.get('threads', [])
        for d in reversed(threads):
            self.queue.put_nowait(self.create_thread(d))

        self.has_more = data.get('has_more', False)
        if self.limit is not None:
            self.limit -= len(threads)
            if self.limit <= 0:
                self.has_more = False

        if self.has_more:
            self.before = self.update_before(threads[-1])

    def create_thread(self, data: ThreadPayload) -> Thread:
        from .threads import Thread
        return Thread(guild=self.guild, state=self.guild._state, data=data)
