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

from typing import TypedDict, Optional, Literal

from .snowflake import Snowflake, SnowflakeList
from .user import User
from .member import MemberWithUser


class ScheduledEventUser(User, total=False):
    guild_member: MemberWithUser


class ScheduledEventMetaData(TypedDict, total=False):
    speaker_ids: SnowflakeList
    location: str

class _ScheduledEventOptional(TypedDict, total=False):
    creator_id: Snowflake
    description: str
    creator: User
    user_count: int


ScheduledEventStatus = Literal[1, 2, 3, 4]
ScheduledEventEntityType = Literal[0, 1, 2, 3]
ScheduledEventPrivacyLevel = Literal[1, 2]


class ScheduledEvent(_ScheduledEventOptional):
    id: Snowflake
    guild_id: Snowflake
    channel_id: Optional[Snowflake]
    name: str
    image: Optional[str]
    scheduled_start_time: str
    scheduled_end_time: str
    privacy_level: ScheduledEventPrivacyLevel
    status: ScheduledEventStatus
    entity_type: ScheduledEventEntityType
    entity_id: Optional[Snowflake]
    entity_metadata: Optional[ScheduledEventMetaData]


class _CreateScheduledEventOptional(TypedDict, total=False):
    channel_id: Snowflake
    entity_metadata: ScheduledEventMetaData
    scheduled_end_time: str
    description: str


class CreateScheduledEvent(_CreateScheduledEventOptional):
    name: str
    privacy_level: ScheduledEventPrivacyLevel
    scheduled_start_time: str
    entity_type: ScheduledEventEntityType


class EditScheduledEvent(TypedDict, total=False):
    channel_id: Optional[Snowflake]
    entity_metadata: Optional[ScheduledEventMetaData]
    name: str
    privacy_level: ScheduledEventPrivacyLevel
    scheduled_start_time: str
    scheduled_end_time: str
    description: str
    entity_type: ScheduledEventEntityType
    status: ScheduledEventStatus
