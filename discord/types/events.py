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

from typing import TypedDict, List, Tuple, Optional

from .snowflake import Snowflake, SnowflakeList
from .member import MemberWithUser
from .emoji import PartialEmoji
from .user import User
from .guild import UnavailableGuild
from .appinfo import PartialAppInfo
from .role import Role
from .threads import Thread, ThreadMember
from .emoji import Emoji
from .sticker import Sticker
from .activity import PartialPresenceUpdate
from .integration import BaseIntegration


class _MessageEventOptional(TypedDict, total=False):
    guild_id: Snowflake


class MessageDeleteEvent(_MessageEventOptional):
    id: Snowflake
    channel_id: Snowflake


class BulkMessageDeleteEvent(_MessageEventOptional):
    ids: List[Snowflake]
    channel_id: Snowflake


class _ReactionActionEventOptional(TypedDict, total=False):
    guild_id: Snowflake
    member: MemberWithUser


class MessageReactionActionEvent(_ReactionActionEventOptional):
    user_id: Snowflake
    channel_id: Snowflake
    message_id: Snowflake
    emoji: PartialEmoji


class _MessageReactionRemoveAllEventOptional(TypedDict, total=False):
    guild_id: Snowflake


class MessageReactionRemoveAllEvent(_MessageReactionRemoveAllEventOptional):
    channel_id: Snowflake
    message_id: Snowflake


class _MessageReactionRemoveEmojiEventOptional(TypedDict, total=False):
    guild_id: Snowflake


class MessageReactionRemoveEmojiEvent(_MessageReactionRemoveEmojiEventOptional):
    channel_id: int
    message_id: int
    emoji: PartialEmoji


class _TypingStartEventOptional(TypedDict, total=False):
    guild_id: Snowflake
    member: MemberWithUser


class TypingStartEvent(_TypingStartEventOptional):
    channel_id: Snowflake
    user_id: Snowflake
    timestamp: int


class _ReadyOptional(TypedDict, total=False):
    # technically a list, but it has a set length
    shard: Tuple[int, int]


class ReadyEvent(_ReadyOptional):
    v: int
    user: User
    guilds: List[UnavailableGuild]
    session_id: str
    application: PartialAppInfo


# add and remove
class GuildBanEvent(TypedDict):
    guild_id: Snowflake
    user: User


class _PartialGuildRoleEvent(TypedDict):
    guild_id: Snowflake


class GuildRoleAddEvent(_PartialGuildRoleEvent):
    role: Role


class GuildRoleUpdateEvent(_PartialGuildRoleEvent):
    role: Role


class GuildRoleRemoveEvent(_PartialGuildRoleEvent):
    role_id: Snowflake


class _ChannelPinsUpdateEventOptional(TypedDict, total=False):
    guild_id: Snowflake
    last_pin_timestamp: str


class ChannelPinsUpdateEvent(_ChannelPinsUpdateEventOptional):
    channel_id: Snowflake


class _ThreadListSyncEventOptional(TypedDict, total=False):
    channel_ids: List[Snowflake]


class ThreadListSyncEvent(_ThreadListSyncEventOptional):
    guild_id: Snowflake
    threads: List[Thread]
    members: List[ThreadMember]


class _ThreadMembersUpdateEventOptional(TypedDict, total=False):
    added_members: List[ThreadMember]
    removed_member_ids: List[Snowflake]


class ThreadMembersUpdateEvent(_ThreadMembersUpdateEventOptional):
    id: Snowflake
    guild_id: Snowflake
    member_count: int


class VoiceServerUpdateEvent(TypedDict):
    token: str
    guild_id: Snowflake
    endpoint: Optional[str]
    channel_id: Snowflake


class WebhooksUpdateEvent(TypedDict):
    guild_id: Snowflake
    channel_id: Snowflake


class GuildMemberAddEvent(MemberWithUser):
    guild_id: Snowflake


class GuildMemberRemoveEvent(TypedDict):
    guild_id: Snowflake
    user: User


class GuildMemberUpdateEvent(MemberWithUser):
    guild_id: Snowflake


class GuildEmojisUpdateEvent(TypedDict):
    guild_id: Snowflake
    emojis: List[Emoji]


class GuildStickersUpdateEvent(TypedDict):
    guild_id: Snowflake
    emojis: List[Sticker]


class _GuildMembersChunkEventOptional(TypedDict, total=False):
    not_found: SnowflakeList
    presences: List[PartialPresenceUpdate]
    nonce: str


class GuildMembersChunkEvent(_GuildMembersChunkEventOptional):
    guild_id: Snowflake
    members: List[MemberWithUser]
    chunk_index: int
    chunk_count: int


class GuildIntegrationsUpdateEvent(BaseIntegration):
    guild_id: Snowflake


class GuildIntegrationCreateEvent(BaseIntegration):
    guild_id: Snowflake


class _GuildIntegrationDeleteEventOptional(TypedDict, total=False):
    application_id: Snowflake


class GuildIntegrationDeleteEvent(_GuildIntegrationDeleteEventOptional):
    id: Snowflake
    guild_id: Snowflake
