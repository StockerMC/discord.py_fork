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

import inspect
import sys
import types
from typing import (
    TYPE_CHECKING,
    Type,
    Any,
    Dict,
    TypeVar,
    List,
    Optional,
    Union,
    ClassVar,
    Tuple,
    Callable,
    Coroutine,
    Final,
    Literal,
    Iterator,
    Generic,
    AsyncGenerator,
    Iterable,
    Set,
    overload,
)

from operator import attrgetter
from .enums import ApplicationCommandType, ApplicationCommandOptionType, InteractionType, ChannelType, InteractionResponseType
from .utils import MISSING, async_all, copy_doc, resolve_annotation, maybe_coroutine
from .member import Member
from .user import User
from .role import Role
from .message import Message, Attachment
from .interactions import Interaction, InteractionResponse, InteractionMessage
from .object import Object
from .guild import Guild
from .channel import TextChannel, StageChannel, VoiceChannel, CategoryChannel, StoreChannel, Thread, PartialMessageable
from .abc import GuildChannel
from .webhook.async_ import async_context

if TYPE_CHECKING:
    from .types.interactions import (
        ApplicationCommand as ApplicationCommandPayload,
        ApplicationCommandOptionChoice as ApplicationCommandOptionChoicePayload,
        ApplicationCommandOption as ApplicationCommandOptionPayload,
        InteractionData,
        ApplicationCommandInteractionDataResolved,
        ApplicationCommandInteractionData,
        ApplicationCommandInteractionDataOption,
    )

    from .state import ConnectionState
    from .webhook import Webhook
    from .permissions import Permissions
    from .client import Client
    from .cog import Cog
    from .embeds import Embed
    from .file import File
    from .ui.view import View
    from .mentions import AllowedMentions

    T = TypeVar('T')
    Coro = Coroutine[Any, Any, T]
    ChannelTypes = Union[
        Type[TextChannel],
        Type[VoiceChannel],
        Type[StageChannel],
        Type[CategoryChannel],
        Type[Thread],
    ]
    ValidOptionTypes = Union[
        Type[str],
        Type[int],
        Type[float],
        Type[Member],
        Type[User],
        Type[Role],
        Type[Object],
        Type[GuildChannel],
        Type[Attachment],
        ChannelTypes,
    ]
    ApplicationCommandKey = Tuple[str, int, Optional['ApplicationCommandKey']]  # name, type, parent
    InteractionChannel = Union[
        VoiceChannel, StageChannel, TextChannel, CategoryChannel, StoreChannel, Thread, PartialMessageable
    ]
    ApplicationCommandOptionChoiceTypes = Union[
        Iterable['ApplicationCommandOptionChoice[int]'],
        Iterable['ApplicationCommandOptionChoice[float]'],
        Iterable['ApplicationCommandOptionChoice[str]'],
    ]
    SlashCommandT = TypeVar('SlashCommandT', bound='SlashCommand')
    AutocompleteCallback = Callable[
        [SlashCommandT, 'AutocompleteResponse[Any]'],
        Union[
            AsyncGenerator[Union['ApplicationCommandOptionChoiceType', 'ApplicationCommandOptionChoice[ApplicationCommandOptionChoiceType]'], None],
            Coro[Iterable[Union['ApplicationCommandOptionChoiceType', 'ApplicationCommandOptionChoice[ApplicationCommandOptionChoiceType]']]]
        ]
    ]
    FuncT = TypeVar('FuncT', bound=Callable[..., Any])


__all__ = (
    'SlashCommand',
    'MessageCommand',
    'UserCommand',
    'SlashCommandResponse',
    'MessageCommandResponse',
    'UserCommandResponse',
    'AutocompleteResponse',
    'ApplicationCommandOption',
    'ApplicationCommandOptionChoice',
    'ApplicationCommandOptions',
    'application_command_option',
)

ClientT = TypeVar('ClientT', bound='Client')
ApplicationCommandOptionChoiceType = TypeVar('ApplicationCommandOptionChoiceType', bound=Union[str, int, float])

PY_310: Final[bool] = sys.version_info >= (3, 10)

OPTION_TYPE_MAPPING: Final[Dict[ValidOptionTypes, ApplicationCommandOptionType]] = {
    str: ApplicationCommandOptionType.string,
    int: ApplicationCommandOptionType.integer,
    float: ApplicationCommandOptionType.number,
    bool: ApplicationCommandOptionType.boolean,
    User: ApplicationCommandOptionType.user,
    Member: ApplicationCommandOptionType.user,
    Role: ApplicationCommandOptionType.role,
    Object: ApplicationCommandOptionType.mentionable,
    GuildChannel: ApplicationCommandOptionType.channel,
    Attachment: ApplicationCommandOptionType.attachment,
}

CHANNEL_TYPE_MAPPING: Final[Dict[ChannelTypes, ChannelType]] = {
    TextChannel: ChannelType.text,
    VoiceChannel: ChannelType.voice,
    StageChannel: ChannelType.stage_voice,
    CategoryChannel: ChannelType.category,
    Thread: ChannelType.public_thread,  # is public_thread correct?
}

OPTION_TYPE_MAPPING.update(dict.fromkeys(CHANNEL_TYPE_MAPPING, ApplicationCommandOptionType.channel))

def _resolve_option_type(option: Union[ValidOptionTypes, ApplicationCommandOptionType]) -> ApplicationCommandOptionType:
    if isinstance(option, ApplicationCommandOptionType):
        return option

    resolved_type = OPTION_TYPE_MAPPING.get(option)
    if resolved_type is None:
        raise TypeError(f'{option!r} is an invalid option type.')

    return resolved_type


class ApplicationCommandOptionChoice(Generic[ApplicationCommandOptionChoiceType]):
    """Represents a choice of an option of an application command.

    .. versionadded:: 2.0

    Attributes
    -----------
    name: :class:`str`
        The name of the choice. This is shown to users.
    value: Union[:class:`str`, :class:`int`, :class:`float`]
        The value of the choice. This is what you will receive if the choice is selected.
        The type of this should be the same type of the option it is for.
    """
    def __init__(self, *, name: str, value: ApplicationCommandOptionChoiceType) -> None:
        if not isinstance(value, (str, int, float)):
            raise TypeError(f'The choice of the option {name!r} must be either a str, int or float not {type(value)!r}.')

        self.name: str = name
        self.value: ApplicationCommandOptionChoiceType = value

    def __repr__(self) -> str:
        return f'<ApplicationCommandOptionChoice name={self.name!r} value={self.value!r}>'

    def to_dict(self) -> ApplicationCommandOptionChoicePayload:
        return {
            'name': self.name,
            'value': self.value,
        }


class ApplicationCommandOption(Generic[ApplicationCommandOptionChoiceType]):
    """Represents an option of a Discord application command.

    .. versionadded:: 2.0

    Attributes
    -----------
    type: :class:`ApplicationCommandOptionType`
        The type of the option.
    name: :class:`str`
        The name of the option.
    description: :class:`str`
        The description of the option.
    required: :class:`bool`
        Whether the option is required or not.
    choices: List[:class:`ApplicationCommandOptionChoice`]
        The choices of the option.
    options: List[:class:`ApplicationCommandOption`]
        The parameters of the option if :attr:`.type` is :attr:`ApplicationCommandOptionType.sub_command` or :attr:`ApplicationCommandOptionType.sub_command_group`.
    default: Any
        The default value for the option. This can be either a value or a callable that takes :class:`SlashCommandResponse` as its
        sole parameter and returns the default value. This callable can be either a regular function or a coroutine function.

        This is for when the option is accessed with it's relevant :class:`ApplicationCommandOptions` instance
        and the option was not provided by the user. If the default was not set and the option was not provided
        by the user and no default was set, the option's value will be ``None``.
    channel_types: Set[:class:`ChannelType`]
        The valid channel types for this option. This is only valid for options of type :attr:`ApplicationCommandOptionType.channel`.
    min_value: Optional[:class:`int`]
        The minimum value permitted for this option.
        This is only valid for options of type :attr:`ApplicationCommandOptionType.integer`.
    max_value: Optional[:class:`int`]
        The maximum value permitted for this option.
        This is only valid for options of type :attr:`ApplicationCommandOptionType.integer`.
    """

    __slots__= (
        'type',
        'name',
        'description',
        'required',
        'choices',
        'options',
        'default',
        'channel_types',
        'min_value',
        'max_value',
        '_autocomplete',
    )
    def __init__(
        self,
        *,
        type: ApplicationCommandOptionType,
        name: str,
        description: str,
        required: bool = MISSING,
        choices: Optional[Iterable[ApplicationCommandOptionChoice[ApplicationCommandOptionChoiceType]]] = None,
        options: Optional[Iterable[ApplicationCommandOption[Union[str, int, float]]]] = None,
        default: Optional[Any] = None,
        channel_types: Optional[Iterable[ChannelType]] = None,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
    ) -> None:
        self.type: ApplicationCommandOptionType = type
        self.name: str = name
        self.description: str = description
        self.required: bool = required
        self.choices: List[ApplicationCommandOptionChoice[ApplicationCommandOptionChoiceType]] = list(choices) if choices is not None else []
        self.options: Iterable[ApplicationCommandOption[Union[str, int, float]]] = options if options is not None else []
        self.default: Optional[Any] = default
        self.channel_types: Set[ChannelType] = set(channel_types) if channel_types is not None else set()
        self.min_value: Optional[Union[int, float]] = min_value
        self.max_value: Optional[Union[int, float]] = max_value
        self._autocomplete: Optional[AutocompleteCallback] = None

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} type={self.type!r} name={self.name!r} description={self.description!r} required={self.required!r}>'

    def autocomplete(
        self, func: AutocompleteCallback[SlashCommandT, ApplicationCommandOptionChoiceType]
    ) -> AutocompleteCallback[SlashCommandT, ApplicationCommandOptionChoiceType]:
        """A decorator that registers a callback for an autocomplete option. 

        The function being registered can be an :data:`typing.AsyncIterator` that yields choices of the same type as the option
        (e.g. :class:`int` if the type of the option is :attr:`ApplicationCommandOption.integer`). The choice can also be an
        :class:`ApplicationCommandOptionChoice` with the appropriate value type. The function can also be a :ref:`coroutine <coroutine>`
        that returns an iterable of choices.

        If a choice is an :class:`ApplicationCommandOptionChoice`, the value must be of type :class:`str`.

        .. note::

            Only options of type :attr:`ApplicationCommandOptionType.string`, :attr:`ApplicationCommandOptionType.integer`,
            and :attr:`ApplicationCommandOptionType.number` can be decorated with this decorator.

        Raises
        -------
        TypeError
            The function being listened to is not a coroutine function or async generator function or the option
            being decorated is not a string, integer, or number option.
        """

        if not inspect.iscoroutinefunction(func) and not inspect.isasyncgenfunction(func):
            raise TypeError('Autocomplete option callbacks must be a coroutine function or async generator function.')

        if self.type not in (ApplicationCommandOptionType.string, ApplicationCommandOptionType.number, ApplicationCommandOptionType.integer):
            raise TypeError('Only string, integer, or number options can be decorated with the autocomplete method')

        self._autocomplete = func
        return func

    async def _define_autocomplete_result(self, *, response: AutocompleteResponse[Any], command: SlashCommand) -> None:
        if self._autocomplete is None:
            return

        result = self._autocomplete(command, response)
        choices: Iterable[Union[str, ApplicationCommandOptionChoiceTypes]]
        if inspect.isasyncgen(result):
            choices = [choice async for choice in result]
        else:
            choices = await result  # type: ignore

        data: Dict[str, Any] = {'choices': []}
        for choice in choices:
            if isinstance(choice, ApplicationCommandOptionChoice):
                name = choice.name
                value = choice.value
            else:
                value = name = choice

            if not isinstance(value, (str, int, float)):
                raise TypeError(f'The value of an autocomplete result choice must be either a str, int, or float not {type(value)!r}')
            
            data['choices'].append({'name': name, 'value': value})

        adapter = async_context.get()
        autocomplete_type = InteractionResponseType.application_command_autocomplete_result.value
        interaction = response.interaction
        await adapter.create_interaction_response(
            interaction.id, token=interaction.token, session=interaction._session, type=autocomplete_type, data=data
        )

    def to_dict(self) -> ApplicationCommandOptionPayload:
        ret: ApplicationCommandOptionPayload = {
            'type': int(self.type),
            'name': self.name,
            'description': self.description,
        }  # type: ignore

        if self.required is not MISSING:
            ret['required'] = self.required

        if self.choices:
            ret['choices'] = [choice.to_dict() for choice in self.choices]

        if self.options:
            ret['options'] = [option.to_dict() for option in self.options]

        if self.channel_types:
            ret['channel_types'] = [type.value for type in self.channel_types]

        if self.max_value:
            ret['max_value'] = self.max_value

        if self.min_value:
            ret['min_value'] = self.min_value

        if self._autocomplete is not None:
            ret['autocomplete'] = True

        return ret


@overload
def application_command_option(
    *,
    description: str,
    name: str = ...,
    type: Union[Literal[ApplicationCommandOptionType.channel], ChannelTypes, Type[GuildChannel]],
    required: bool = ...,
    default: Optional[Any] = ...,
    channel_types: Optional[Iterable[Union[ChannelType, ChannelTypes]]] = ...,
) -> ApplicationCommandOption[Any]: ...

@overload
def application_command_option(
    *,
    description: str,
    name: str = ...,
    type: Union[Literal[ApplicationCommandOptionType.integer], Type[int]],
    required: bool = ...,
    choices: Optional[List[ApplicationCommandOptionChoice[int]]] = ...,
    default: Optional[Any] = ...,
    min_value: Optional[int] = ...,
    max_value: Optional[int] = ...,
) -> ApplicationCommandOption[int]: ...

@overload
def application_command_option(
    *,
    description: str,
    name: str = ...,
    type: Union[Literal[ApplicationCommandOptionType.number], Type[float]],
    required: bool = ...,
    choices: Optional[List[ApplicationCommandOptionChoice[float]]] = ...,
    default: Optional[Any] = ...,
    min_value: Optional[float] = ...,
    max_value: Optional[float] = ...,
) -> ApplicationCommandOption[float]: ...

@overload
def application_command_option(
    *,
    description: str,
    name: str = ...,
    type: Union[Literal[ApplicationCommandOptionType.string], Type[str]],
    required: bool = ...,
    choices: Optional[List[ApplicationCommandOptionChoice[str]]] = ...,
    default: Optional[Any] = ...,
) -> ApplicationCommandOption[str]: ...

@overload
def application_command_option(
    *,
    description: str,
    name: str = ...,
    type: Union[Type[Member], Type[User], Type[Role]],
    required: bool = ...,
    default: Optional[Any] = ...,
) -> Any: ...

@overload
def application_command_option(
    *,
    description: str,
    name: str = ...,
    required: bool = ...,
    min_value: Optional[int] = ...,
    max_value: Optional[int] = ...,
    choices: List[ApplicationCommandOptionChoice[int]] = ...,
    default: Optional[Any] = ...,
) -> Any: ...

@overload
def application_command_option(
    *,
    description: str,
    name: str = ...,
    required: bool = ...,
    choices: List[ApplicationCommandOptionChoice[float]] = ...,
    default: Optional[Any] = ...,
    min_value: Optional[float] = ...,
    max_value: Optional[float] = ...,
) -> Any: ...

@overload
def application_command_option(
    *,
    description: str,
    name: str = ...,
    required: bool = ...,
    choices: List[ApplicationCommandOptionChoice[str]],
    default: Optional[Any] = ...,
) -> Any: ...

def application_command_option(
    *,
    description: str,
    name: str = MISSING,
    type: Union[ApplicationCommandOptionType, ValidOptionTypes] = MISSING,
    required: bool = True,
    choices: Optional[ApplicationCommandOptionChoiceTypes] = None,
    default: Optional[Any] = None,
    channel_types: Optional[Iterable[Union[ChannelType, ChannelTypes]]] = None,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
) -> Any:
    r"""Used for creating an option for an application command.

    To avoid type checker errors when using this with typehints,
    the return type is ``Any`` if the ``type`` parameter is not
    set.

    .. note::

        If this is used in a class with a channel typehint (excluding :class:`.abc.GuildChannel`),
        the channel types of the option will be set to the class being typehinted. In the case of a
        :data:`typing.Union` typehint of channel types, the channel types of the option will be set
        to that.

    .. versionadded:: 2.0

    Parameters
    -----------
    description: :class:`str`
        The description of the option.
    name: :class:`str`
        The name of the option.
    type: Union[:class:`ApplicationCommandOptionType`, Type]
        The type of the option. This can be an :class:`ApplicationCommandOptionType` member or a :ref:`Discord model <discord_api_models>`.
        Note that not all Discord models are acceptable types.
    required: :class:`bool`
        Whether the option is required or not.
        Defaults to ``True``.
    choices: Optional[Iterable[:class:`ApplicationCommandOptionChoice`]]
        The choices of the option, if any.
    default: Any
        The default value for the option. This can be either a value or a callable that takes :class:`SlashCommandResponse` as its
        sole parameter and returns the default value. This callable can be either a regular function or a coroutine function.

        This is for when the option is accessed with it's relevant :class:`ApplicationCommandOptions` instance
        and the option was not provided by the user. If the default was not set and the option was not provided
        by the user and no default was set, the option's value will be ``None``.
    channel_types: Optional[Iterable[Union[:class:`ChannelType`, Type]]]
        The valid channel types for this option. This is only valid for options of type :attr:`ApplicationCommandOptionType.channel`

        This can including the following: :class:`ChannelType` members, :class:`TextChannel`, :class:`VoiceChannel`,
        :class:`StageChannel`, :class:`CategoryChannel` and :class:`Thread`.
    min_value: Optional[:class:`int`]
        The minimum value permitted for this option.
        This is only valid for options of type :attr:`ApplicationCommandOptionType.integer`.
    max_value: Optional[:class:`int`]
        The maximum value permitted for this option.
        This is only valid for options of type :attr:`ApplicationCommandOptionType.integer`.

    Returns
    --------
    :class:`ApplicationCommandOption`
        The created application command option.
    """
    if type is not MISSING:
        resolved_type = _resolve_option_type(type)
    else:
        resolved_type = MISSING

    if choices is not None:
        for choice in choices:
            if not isinstance(choice, ApplicationCommandOptionChoice):
                raise TypeError(f'choices must only contain ApplicationCommandOptionChoice instances, not {choice.__class__.__name__}')

    if default is not None:
        if hasattr(default, '__discord_application_command_option_default__') and inspect.isclass(default):
            default = default()

    if channel_types is not None:
        resolved_channel_types = [CHANNEL_TYPE_MAPPING[channel_type] if not isinstance(channel_type, ChannelType) else channel_type for channel_type in channel_types]
    else:
        resolved_channel_types = channel_types

    return ApplicationCommandOption(
        name=name,
        description=description,
        type=resolved_type,
        required=required,
        choices=choices,
        default=default,
        channel_types=resolved_channel_types,
        min_value=min_value,
        max_value=max_value,
    )

def _transform_literal_choices(
    attr_name: str,
    attr_type: ApplicationCommandOptionType,
    annotation: Any
) -> Tuple[Any, ApplicationCommandOptionChoiceTypes]:
    annotation_type = MISSING
    choices: ApplicationCommandOptionChoiceTypes = []
    for arg in annotation.__args__:
        arg_type = type(arg)
        if arg_type not in (str, int, float):
            raise TypeError(f'The choice of the option {attr_name!r} must be either a str, int, or float not {type(arg_type)!r}.')

        if annotation_type is not MISSING and arg_type is not annotation_type:
            raise TypeError(f'The choices for the option {attr_name!r} must be the same type (str, int or float).')

        if attr_type is not MISSING and arg_type is not annotation_type:
            raise TypeError(f'The type of the choices of the option {attr_name!r} must be the same as the type of the option.')

        annotation_type = arg_type
        choices.append(ApplicationCommandOptionChoice(name=str(arg), value=arg))

    return (annotation_type, choices)


def _get_options(
    attr_namespace: Dict[str, Any],
    annotation_namespace: Dict[str, Any],
    globals: Dict[str, Any],
    locals: Dict[str, Any],
) -> Dict[str, ApplicationCommandOption[Union[str, int, float]]]:
    options: Dict[str, ApplicationCommandOption] = {}
    cache: Dict[str, Any] = {}
    for attr_name, attr in attr_namespace.items():
        if not isinstance(attr, ApplicationCommandOption):
            continue

        if attr_name in annotation_namespace:
            annotation = resolve_annotation(annotation_namespace[attr_name], globals, locals, cache)
            annotation_type = MISSING
            origin = getattr(annotation, '__origin__', None)
            is_union = origin is Union or PY_310 and annotation.__class__ is types.UnionType  # type: ignore
            args = []

            if is_union:
                args = list(annotation.__args__)
                if type(None) in args:
                    attr.required = False
                    args.remove(type(None))

                for arg in args:
                    annotation_type = arg
                    nested_origin = getattr(arg, '__origin__', None)
                    if nested_origin is Literal:
                        annotation_type, choices = _transform_literal_choices(attr_name, attr.type, arg)
                        attr.choices.extend(choices)

                    channel_type = CHANNEL_TYPE_MAPPING.get(arg)
                    if channel_type is not None:
                        attr.channel_types.add(channel_type)

            elif origin is Literal:
                annotation_type, choices = _transform_literal_choices(attr_name, attr.type, annotation)
                attr.choices.extend(choices)

            else:
                annotation_type = annotation

            resolved_option_type = _resolve_option_type(annotation_type)

            if attr.type is MISSING:
                attr.type = resolved_option_type

            channel_type = CHANNEL_TYPE_MAPPING.get(annotation)
            if channel_type is not None:
                attr.channel_types.add(channel_type)

        if attr.name is MISSING:
            attr.name = attr_name

        if attr.type is MISSING:
            raise TypeError(f'The type of the option {attr.name!r} must be set.')

        options[attr_name] = attr

    return options


class ApplicationCommandOptions:
    """Represents the received options of an application command.

    This type can be accessed from :attr:`SlashCommandResponse.options`.

    The attributes of an ``ApplicationCommandOptions`` instance are the options of the
    application command it is for. If an option is not required and was not provided,
    it will be ``None``.

    For example:

    .. code-block:: python3

        class Avatar(discord.SlashCommand):
            user: discord.Member = discord.application_command_option(description='The user to get the avatar from')

            async def callback(self, response: discord.SlashCommandResponse):
                user = response.options.user
                # user will be a `discord.Member`, or a `discord.User` in DMs with the bot
                await response.send_message(user.display_avatar, ephemeral=True)

    .. container:: operations

        .. describe:: x == y

            Checks if two :class:`ApplicationCommandOptions` are equal. This checks if both instances 
            have the same provided options with the same values.

        .. describe:: x != y

            Checks if two :class:`ApplicationCommandOptions` are not equal.

        .. describe:: bool(x)

            Returns whether any options were provided.

        .. describe:: hash(x)

            Return the :class:`ApplicationCommandOptions`'s hash.

        .. describe:: iter(x)

            Returns an iterator of ``(option, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.

        .. describe:: len(x)

            Returns the number of options provided.

        .. describe:: y in x

            Checks if the option name ``y`` was provided.
    """
    def __init__(
        self,
        *,
        guild_id: Optional[int],
        options: Optional[List[ApplicationCommandInteractionDataOption]],
        resolved_data: Optional[ApplicationCommandInteractionDataResolved],
        state: ConnectionState,
        command_options: List[ApplicationCommandOption[Union[str, int, float]]],
    ) -> None:
        self.__application_command_options__: Dict[str, Any] = {option.name: None for option in command_options if not option.required}
        if options is None:
            return

        options = options[:]  # make a copy so we don't modify the original list

        while options:
            option = options.pop(0)
            nested_options = option.get('options')
            if nested_options is not None:
                options.extend(nested_options)
                continue

            # the option is the focused option in an autocomplete response
            if option.get('focused'):
                continue

            value: Any = option.get('value')
            # the option is a subcommand
            if value is None:
                continue

            resolved_data = resolved_data or {}
            option_type = option['type']

            if option_type == 6:  # user
                try:
                    resolved_user = resolved_data['users'][value]
                except KeyError:
                    resolved_user = None

                if guild_id is not None:
                    guild = state._get_guild(guild_id)
                    user = guild and guild.get_member(int(value)) or state.get_user(int(value))
                    if user is None:
                        if resolved_user is not None:
                            try:
                                member_with_user = {**resolved_data['members'][value], 'user': resolved_user}  # type: ignore
                                value = Member(state=state, data=member_with_user, guild=guild or Object(id=guild_id))  # type: ignore
                            except KeyError:
                                value = User(state=state, data=resolved_user)
                        else:
                            value = Object(id=int(value))
                    else:
                        value = user
                else:
                    if resolved_user is not None:
                        value = User(state=state, data=resolved_user)
                    else:
                        value = Object(id=int(value))
            elif option_type == 7:  # channel
                guild = state._get_guild(guild_id)
                if guild is not None:
                    channel = guild._resolve_channel(int(value))
                    if channel is None:  # there isn't enough data in the resolved channels from the payload
                        channel = PartialMessageable(state=state, id=int(value))

                    value = channel
                else:
                    value = PartialMessageable(state=state, id=int(value))
            elif option_type == 8:  # role
                guild = state._get_guild(guild_id)
                role = guild and guild.get_role(int(value))
                if role is None:
                    try:
                        resolved_role = resolved_data['roles'][value]
                        value = Role(guild=guild or Object(id=guild_id), state=state, data=resolved_role)  # type: ignore
                    except KeyError:
                        value = Object(id=int(value))
                else:
                    value = role
            elif option_type == 9:  # mention (role or user)
                if guild_id is not None:
                    guild = state._get_guild(guild_id)
                    try:
                        obj = guild and guild.get_member(int(value))
                        if obj is None:
                            try:
                                resolved_user = resolved_data['users'][value]
                                member_with_user = {**resolved_data['members'][value], 'user': resolved_user}  # type: ignore
                                value = Member(state=state, data=member_with_user, guild=guild)  # type: ignore
                            except KeyError:
                                value = Object(id=int(value))
                        else:
                            value = obj
                    except KeyError:
                        obj = guild and guild.get_role(int(value))
                        if obj is None:
                            try:
                                resolved_role = resolved_data['roles'][value]
                                value = Role(guild=guild or Object(id=guild_id), state=state, data=resolved_role)  # type: ignore
                            except KeyError:
                                value = Object(id=int(value))
                        else:
                            value = obj
                else:
                    obj = state.get_user(int(value))
                    if obj is None:
                        try:
                            value = User(state=state, data=resolved_data['users'][value])
                        except KeyError:
                            value = Object(id=int(value))
                    else:
                        value = obj
            elif option_type == 11:  # attachment
                resolved_attachment = resolved_data['attachments'][value]  # type: ignore
                value = Attachment(data=resolved_attachment, state=state)

            self.__application_command_options__[option['name']] = value

    def __repr__(self) -> str:
        inner = ', '.join([f'{k}={v!r}' for k, v in self.__application_command_options__.items()])
        return f'{self.__class__.__name__}({inner})'

    def __getattr__(self, name: str) -> Any:
        try:
            return self.__application_command_options__[name]
        except KeyError:
            raise AttributeError(name) from None

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.__application_command_options__ == other.__application_command_options__

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __bool__(self) -> bool:
        return bool(self.__len__())

    def __hash__(self) -> int:
        return hash(self.__application_command_options__)

    def __len__(self) -> int:
        return len([v for v in self.__application_command_options__.values() if v is not None])

    def __contains__(self, option: str) -> bool:
        return option in self.__application_command_options__ and option is not None

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        yield from self.__application_command_options__.items()

def _get_used_subcommand(options: List[ApplicationCommandInteractionDataOption]) -> Optional[str]:
    while options:
        option = options.pop(0)
        if option['type'] == 1:
            return option['name']

        if option['type'] == 2:
            options.append(option.get('options'))  # type: ignore
            continue

        return None

    return None


# the original function is flatten_user in member.py
def flatten(original_cls: type, original_attr: str) -> Callable[[Type[T]], Type[T]]:
    def decorator(cls: Type[T]) -> Type[T]:
        for attr, value in original_cls.__dict__.items():

            # ignore private/special methods
            if attr.startswith('_'):
                continue

            # don't override what we already have
            if attr in cls.__dict__:
                continue

            # if it's a slotted attribute or a property, redirect it
            # slotted members are implemented as member_descriptors in Type.__dict__
            if not hasattr(value, '__annotations__'):
                getter = attrgetter(f'{original_attr}.{attr}')
                setattr(cls, attr, property(getter, doc=f'Equivalent to :attr:`{original_cls.__name__}.{attr}`'))
            else:
                # Technically, this can also use attrgetter
                # However I'm not sure how I feel about "functions" returning properties
                # It probably breaks something in Sphinx.
                # probably a member function by now
                def generate_function(x):
                    # We want sphinx to properly show coroutine functions as coroutines
                    if inspect.iscoroutinefunction(value):

                        async def general(self, *args, **kwargs):  # type: ignore
                            return await getattr(self.interaction if original_attr == 'interaction' else self.interaction.response, x)(*args, **kwargs)

                    else:

                        def general(self, *args, **kwargs):
                            return getattr(self.interaction if original_attr == 'interaction' else self.interaction.response, x)(*args, **kwargs)

                    general.__name__ = x
                    return general

                func = generate_function(attr)
                func = copy_doc(value)(func)
                setattr(cls, attr, func)

        return cls

    return decorator


@flatten(Interaction, 'interaction')
@flatten(InteractionResponse, 'interaction.response')
class BaseApplicationCommandResponse(Generic[ClientT]):
    if TYPE_CHECKING:
        command: BaseApplicationCommand
        # interaction attributes
        id: int
        type: InteractionType
        data: Optional[InteractionData]
        token: str
        locale: Optional[str]
        guild_locale: Optional[str]
        version: int
        channel_id: Optional[int]
        guild_id: Optional[int]
        application_id: int
        message: Optional[Message]
        user: Optional[Union[User, Member]]
        client: ClientT
        # properties
        @property
        def guild(self) -> Optional[Guild]: ...
        def channel(self) -> Optional[InteractionChannel]: ...
        @property
        def permissions(self) -> Permissions: ...
        @property
        def response(self) -> InteractionResponse: ...
        @property
        def followup(self) -> Webhook: ...
        # interaction/interaction response methods
        async def original_message(self) -> InteractionMessage: ...
        @overload
        async def edit_original_message(  # type: ignore
            self,
            *,
            content: Optional[str] = MISSING,
            embed: Optional[Embed] = MISSING,
            file: File = MISSING,
            view: Optional[View] = MISSING,
            allowed_mentions: Optional[AllowedMentions] = None,
        ) -> InteractionMessage: ...
        @overload
        async def edit_original_message(
            self,
            *,
            content: Optional[str] = MISSING,
            embed: Optional[Embed] = MISSING,
            files: List[File] = MISSING,
            view: Optional[View] = MISSING,
            allowed_mentions: Optional[AllowedMentions] = None,
        ) -> InteractionMessage: ...
        @overload
        async def edit_original_message(
            self,
            *,
            content: Optional[str] = MISSING,
            embeds: List[Embed] = MISSING,
            file: File = MISSING,
            view: Optional[View] = MISSING,
            allowed_mentions: Optional[AllowedMentions] = None,
        ) -> InteractionMessage: ...
        @overload
        async def edit_original_message(
            self,
            *,
            content: Optional[str] = MISSING,
            embeds: List[Embed] = MISSING,
            files: List[File] = MISSING,
            view: Optional[View] = MISSING,
            allowed_mentions: Optional[AllowedMentions] = None,
        ) -> InteractionMessage: ...
        async def delete_original_message(self) -> None: ...
        def is_done(self) -> bool: ...
        async def defer(self, *, ephemeral: bool = False) -> None: ...
        async def pong(self) -> None: ...
        @overload
        async def send_message(  # type: ignore
            self,
            content: Optional[Any] = None,
            *,
            embed: Embed = MISSING,
            view: View = MISSING,
            tts: bool = False,
            ephemeral: bool = False,
            allowed_mentions: Optional[AllowedMentions] = None,
        ) -> None: ...
        @overload
        async def send_message(
            self,
            content: Optional[Any] = None,
            *,
            embed: Embed = MISSING,
            file: File = MISSING,
            view: View = MISSING,
            tts: bool = False,
            ephemeral: bool = False,
            allowed_mentions: Optional[AllowedMentions] = None,
        ) -> None: ...
        @overload
        async def send_message(
            self,
            content: Optional[Any] = None,
            *,
            embed: Embed = MISSING,
            files: List[File] = MISSING,
            view: View = MISSING,
            tts: bool = False,
            ephemeral: bool = False,
            allowed_mentions: Optional[AllowedMentions] = None,
        ) -> None: ...
        @overload
        async def send_message(
            self,
            content: Optional[Any] = None,
            *,
            embeds: List[Embed] = MISSING,
            view: View = MISSING,
            tts: bool = False,
            ephemeral: bool = False,
            allowed_mentions: Optional[AllowedMentions] = None,
        ) -> None: ...
        @overload
        async def send_message(
            self,
            content: Optional[Any] = None,
            *,
            embeds: List[Embed] = MISSING,
            file: File = MISSING,
            view: View = MISSING,
            tts: bool = False,
            ephemeral: bool = False,
            allowed_mentions: Optional[AllowedMentions] = None,
        ) -> None: ...
        @overload
        async def send_message(
            self,
            content: Optional[Any] = None,
            *,
            embeds: List[Embed] = MISSING,
            files: List[File] = MISSING,
            view: View = MISSING,
            tts: bool = False,
            ephemeral: bool = False,
            allowed_mentions: Optional[AllowedMentions] = None,
        ) -> None: ...
        @overload
        async def edit_message(  # type: ignore
            self,
            *,
            content: Optional[Any] = MISSING,
            embed: Optional[Embed] = MISSING,
            attachments: List[Attachment] = MISSING,
            view: Optional[View] = MISSING,
        ) -> None: ...
        @overload
        async def edit_message(
            self,
            *,
            content: Optional[Any] = MISSING,
            embeds: List[Embed] = MISSING,
            attachments: List[Attachment] = MISSING,
            view: Optional[View] = MISSING,
        ) -> None: ...


class SlashCommandResponse(BaseApplicationCommandResponse[ClientT]):
    """A class that represents the response from a slash command.

    .. versionadded:: 2.0

    Attributes
    -----------
    interaction: :class:`Interaction`
        The interaction of the response.
    options: :class:`ApplicationCommandOptions`
        The options of the slash command used.
    command: :class:`SlashCommand`
        The slash command used.
    """
    def __init__(self, interaction: Interaction[ClientT], options: ApplicationCommandOptions, command: SlashCommand) -> None:
        self.interaction: Interaction[ClientT] = interaction
        self.options: ApplicationCommandOptions = options
        self.command: SlashCommand = command


class MessageCommandResponse(BaseApplicationCommandResponse[ClientT]):
    """A class that represents the response from a message command.

    .. versionadded:: 2.0

    Attributes
    -----------
    interaction: :class:`Interaction`
        The interaction of the response.
    target: :class:`Message`
        The message the command was used on.
    command: :class:`MessageCommand`
        The message command used.
    """
    def __init__(self, interaction: Interaction[ClientT], target: Message, command: MessageCommand) -> None:
        self.interaction: Interaction[ClientT] = interaction
        self.target: Message = target
        self.command: MessageCommand = command


class UserCommandResponse(BaseApplicationCommandResponse[ClientT]):
    """A class that represents the response from a message command.

    .. versionadded:: 2.0

    Attributes
    -----------
    interaction: :class:`Interaction`
        The interaction of the response.
    target: Union[:class:`User`, :class:`Member`]
        The user or member the command was used on.
    command: :class:`UserCommand`
        The user command used.
    """
    def __init__(self, interaction: Interaction[ClientT], target: Union[Member, User], command: UserCommand) -> None:
        self.interaction: Interaction[ClientT] = interaction
        self.target: Union[Member, User] = target
        self.command: UserCommand = command


class AutocompleteResponse(BaseApplicationCommandResponse[ClientT]):
    """A class that represents the response from a user typing an autocomplete option.

    .. versionadded:: 2.0

    Attributes
    -----------
    interaction: :class:`Interaction`
        The interaction of the response.
    value: :class:`str`
        The data the user is typing.
    command: :class:`SlashCommand`
        The slash command used.
    options: :class:`ApplicationCommandOptions`
        The options of the slash command used.
    """

    def __init__(self, interaction: Interaction[ClientT], options: ApplicationCommandOptions, command: SlashCommand, value: str) -> None:
        self.interaction: Interaction[ClientT] = interaction
        self.options: Any = options
        self.value: str = value
        self.command: SlashCommand = command


def _traverse_mro_for_attr(cls: type, attr_name: str, default: T = MISSING) -> Union[T, Any]:
    attr = default
    for base in reversed(cls.__mro__):
        attr = getattr(base, attr_name, default)
        if attr is default:
            continue

        break

    return attr


def _application_command_special_method(func: FuncT) -> FuncT:
    func.__application_command_special_method__ = None
    return func


def _get_overridden_method(method: FuncT) -> Optional[FuncT]:
    """Return None if the method is not overridden. Otherwise returns the overridden method."""
    return getattr(method.__func__, '__application_command_special_method__', method)


class BaseApplicationCommand:
    if TYPE_CHECKING:
        __application_command_options__: ClassVar[Dict[str, ApplicationCommandOption[Union[str, int, float]]]]
        __application_command_name__: ClassVar[str]
        __application_command_description__: ClassVar[str]
        __application_command_type__: ClassVar[ApplicationCommandType]
        __application_command_default_permission__: ClassVar[bool]
        __application_command_group_command__: ClassVar[bool]
        __application_command_subcommands__: ClassVar[Dict[str, SlashCommand]]
        __application_command_parent__: Optional[Union[Type[SlashCommand], SlashCommand]]
        __application_command_guild_ids__: Optional[List[int]]
        __application_command_global_command__: bool

    __discord_application_command__: ClassVar[bool] = True

    # attribute: key to display
    __application_command_repr_attrs__: Dict[str, str] = {
        '__application_command_name__': 'name',
        '__application_command_type__': 'type',
    }
    _cog: Optional[Cog] = None

    @overload
    def __init_subclass__(
        cls,
        *,
        name: Optional[str] = None,
        description: str = MISSING,
        parent: Optional[Type[SlashCommand]] = None,
        type: ApplicationCommandType = MISSING,
        default_permission: bool = True,
        guild_ids: Optional[List[int]] = None,
        global_command: Literal[False] = ...,
        group: bool = False,
    ) -> None:
        ...

    @overload
    def __init_subclass__(
        cls,
        *,
        name: Optional[str] = None,
        description: str = MISSING,
        parent: Optional[Type[SlashCommand]] = None,
        type: ApplicationCommandType = MISSING,
        default_permission: bool = True,
        global_command: Literal[True],
        group: bool = False,
    ) -> None:
        ...

    def __init_subclass__(
        cls,
        *,
        name: Optional[str] = None,
        description: str = MISSING,
        parent: Optional[Type[SlashCommand]] = None,  # make this SlashCommand?
        type: ApplicationCommandType = MISSING,
        default_permission: bool = True,
        guild_ids: Optional[List[int]] = None,
        global_command: bool = MISSING,
        group: bool = False,
    ) -> None:
        if type is MISSING:
            type = _traverse_mro_for_attr(cls, '__application_command_type__')

        if name is None:
            name = cls.__name__

        if type is ApplicationCommandType.slash:
            name = name.lower()

        if description is MISSING:
            doc = cls.__doc__
            if doc is not None:
                description = inspect.cleandoc(doc)

        if parent is not None:
            if parent.__application_command_type__ is not ApplicationCommandType.slash:
                raise TypeError(f'parent must derive from SlashCommand not {parent.__name__}')

            if type is not ApplicationCommandType.slash:
                raise TypeError('Only slash commands can have parents')

        if type is not MISSING and not isinstance(type, ApplicationCommandType):
            raise TypeError(f'type must be an ApplicationCommandType member not {type.__class__.__name__}') # is member the right word here

        # inspired/copied from FlagsMeta
        try:
            global_ns = sys.modules[cls.__module__].__dict__
        except KeyError:
            global_ns = {}

        frame = inspect.currentframe()
        try:
            if frame is None:
                local_ns = {}
            else:
                if frame.f_back is None:
                    local_ns = frame.f_locals
                else:
                    local_ns = frame.f_back.f_locals
        finally:
            del frame

        cls_dict = dict(cls.__dict__)  # make a copy
        attrs_to_remove = ['__module__', '__doc__', '__annotations__']
        for attr in attrs_to_remove:
            cls_dict.pop(attr, None)

        options = _get_options(cls_dict, cls.__annotations__, global_ns, local_ns)

        cls.__application_command_options__ = options
        cls.__application_command_name__ = name

        cls.__application_command_description__ = description
        cls.__application_command_parent__ = parent
        cls.__application_command_type__ = type
        cls.__application_command_default_permission__ = bool(default_permission)
        cls.__application_command_guild_ids__ = guild_ids
        if global_command is MISSING:
            global_command = not guild_ids

        cls.__application_command_global_command__ = global_command
        cls.__application_command_group_command__ = group
        cls.__application_command_subcommands__ = {}

        if parent is not None:
            # it gets set as an instance later
            parent.__application_command_subcommands__[name] = cls  # type: ignore

    def __repr__(self) -> str:
        attrs = ' '.join([f'{display_key}={getattr(self, key)!r}' for key, display_key in self.__application_command_repr_attrs__.items()])
        return f'<{self.__class__.__name__} {attrs}>'

    def __str__(self) -> str:
        return self.__application_command_name__

    @classmethod
    def _get_key(cls) -> ApplicationCommandKey:
        return (
            cls.__application_command_name__,
            int(cls.__application_command_type__),
            cls.__application_command_parent__._get_key() if cls.__application_command_parent__ is not None else None
        )

    @classmethod
    def _recursively_get_subcommand(cls, name: str) -> Optional[BaseApplicationCommand]:
        subcommands = list(cls.__application_command_subcommands__.values())
        for subcommand in subcommands:
            if subcommand.__application_command_name__ == name:
                return subcommand

            if name in subcommand.__application_command_subcommands__:
                return subcommand.__application_command_subcommands__[name]

        return None

    def _get_used_command(
        self, application_command_data: ApplicationCommandInteractionData, guild_id: Optional[int]
    ) -> Optional[BaseApplicationCommand]:
        command_name = application_command_data['name']
        command_type = application_command_data['type']
        # check if the guild id is not correct (if it's not a global command)
        # or if the command name or type does not match
        if (
            not self.__application_command_global_command__ and guild_id is not None
            and self.__application_command_guild_ids__ is not None and guild_id not in self.__application_command_guild_ids__
            or self.__application_command_name__ != command_name or int(self.__application_command_type__) != command_type
        ):
            return None

        options = application_command_data.get('options')
        if options is not None:
            if self.__application_command_subcommands__:
                used_subcommand = _get_used_subcommand(options.copy())
                if used_subcommand is not None:
                    return self._recursively_get_subcommand(used_subcommand)

        return self

    @classmethod
    def _as_option(cls) -> ApplicationCommandOption:
        type = ApplicationCommandOptionType.sub_command_group if cls.__application_command_group_command__ else ApplicationCommandOptionType.sub_command
        return ApplicationCommandOption(
            type=type,
            name=cls.__application_command_name__,
            description=cls.__application_command_description__,
            options=list(cls.__application_command_options__.values()),
        )

    async def _scheduled_task(self, response: BaseApplicationCommandResponse[Any], client: Client) -> None:
        from .cog import Cog  # circular import
        cog = self._cog
        try:
            if isinstance(response, SlashCommandResponse):
                for option in self.__application_command_options__.values():
                    default = option.default
                    # check if the option is optional, a default was set and that a value wasn't provided
                    if not option.required and default is not None and getattr(response.options, option.name, None) is None:
                        if callable(default):
                            default = await maybe_coroutine(default, response)

                        response.options.__application_command_options__[option.name] = default

            # the response type is correct
            global_allow = await async_all(f(response) for f in client._application_command_checks)  # type: ignore
            if not global_allow:
                return

            if cog is not None:
                cog_check = Cog._get_overridden_method(cog.cog_application_command_check)
                if cog_check is not None:
                    # the response type is correct
                    cog_allow = await cog_check(response)  # type: ignore
                    if not cog_allow:
                        return

            command_check = _get_overridden_method(self.command_check)
            parent = self.__application_command_parent__
            while command_check is None and parent is not None:
                command_check = _get_overridden_method(parent.command_check)
                parent = parent.__application_command_parent__

            if command_check is not None:
                # parents of the command will be instances, so we don't have to provide self
                allow = await command_check(response)  # type: ignore
                if not allow:
                    return

            await self.callback(response)
            if not response.response._responded:
                await response.defer()
        except Exception as e:
            try:
                if cog is not None:
                    cog_error_handler = Cog._get_overridden_method(cog.cog_application_command_error)
                    if cog_error_handler is not None:
                        # the response type is correct
                        await cog_error_handler(response, e)  # type: ignore
            finally:
                client.dispatch('application_command_error', response, e)
                on_error = _get_overridden_method(self.on_error)
                parent = self.__application_command_parent__
                while on_error is None and parent is not None:
                    on_error = _get_overridden_method(parent.on_error)
                    parent = parent.__application_command_parent__

                if on_error is not None:
                    # parents of the command will be instances, so we don't have to provide self
                    await on_error(response, e)  # type: ignore

    @classmethod
    def set_name(cls, name: str) -> None:
        """Sets the name of the application command.

        Parameters
        -----------
        name: :class:`str`
            The description of the application command.
        """
        cls.__application_command_name__ = str(name)

    @classmethod
    def set_type(cls, type: ApplicationCommandType) -> None:
        """Sets the type of the application command.

        Parameters
        -----------
        type: :class:`ApplicationCommandType`
            The type of the application command.
        """
        if not isinstance(type, ApplicationCommandType):
            raise TypeError(f'type must be an ApplicationCommandType member not {type.__class__.__name__}')

        cls.__application_command_type__ = type

    async def callback(self, response: BaseApplicationCommandResponse[Any]) -> None:
        pass

    @_application_command_special_method
    async def command_check(self, response: BaseApplicationCommandResponse[Any]) -> bool:
        return True

    @_application_command_special_method
    async def on_error(self, response: BaseApplicationCommandResponse[Any], error: Exception) -> None:
        pass

    @classmethod
    def to_dict(cls) -> ApplicationCommandPayload:
        ret: ApplicationCommandPayload = {
            'name': cls.__application_command_name__,
            'type': int(cls.__application_command_type__),
            'default_permission': cls.__application_command_default_permission__,
        }  # type: ignore

        if cls.__application_command_type__ is ApplicationCommandType.slash:
            description = cls.__application_command_description__
            if description is MISSING:
                raise TypeError('Slash commands must have a description.')

            ret['description'] = description

            extra = []
            for command in cls.__application_command_subcommands__.values():
                type = ApplicationCommandOptionType.sub_command_group if command.__application_command_group_command__ else ApplicationCommandOptionType.sub_command
                extra.append(ApplicationCommandOption(
                    type=type,
                    name=command.__application_command_name__,
                    description=command.__application_command_description__,
                    options=[
                        *command.__application_command_options__.values(),
                        *[subcommand._as_option() for subcommand in command.__application_command_subcommands__.values()],
                    ],
                ))
                
            options = sorted([*cls.__application_command_options__.values(), *extra], key=lambda o: not o.required)  # required options have to come before optional options
            if options:
                options = [option.to_dict() for option in options]
                ret['options'] = options

        return ret

    @property
    def name(self) -> str:
        return self.__application_command_name__

    @property
    def description(self) -> str:
        return self.__application_command_description__

    @property
    def options(self) -> List[ApplicationCommandOption[Union[str, int, float]]]:
        return list(self.__application_command_options__.values())

    @property
    def type(self) -> ApplicationCommandType:
        return self.__application_command_type__

    @property
    def default_permission(self) -> bool:
        return self.__application_command_default_permission__

    @property
    def group_command(self) -> bool:
        return self.__application_command_group_command__

    @property
    def subcommands(self) -> List[Union[Type[SlashCommand], SlashCommand]]:
        return list(self.__application_command_subcommands__.values())

    @property
    def parent(self) -> Optional[Union[SlashCommand, Type[SlashCommand]]]:
        return self.__application_command_parent__

    @property
    def guild_ids(self) -> Optional[List[int]]:
        return self.__application_command_guild_ids__

    @property
    def global_command(self) -> bool:
        return self.__application_command_global_command__

    @property
    def full_parent_name(self) -> str:
        entries = []
        command = self
        while command.__application_command_parent__ is not None:
            command = command.__application_command_parent__
            entries.append(command.__application_command_name__)

        return ' '.join(reversed(entries))

    @property
    def qualified_name(self) -> str:
        parent = self.full_parent_name
        if parent:
            return parent + ' ' + self.__application_command_name__
        else:
            return self.__application_command_name__

class SlashCommand(BaseApplicationCommand, type=ApplicationCommandType.slash):
    """Represents a Discord slash command.

    .. versionadded:: 2.0    
    """
    
    __application_command_repr_attrs__: Dict[str, str] = {  # actual key: key to display
        '__application_command_name__': 'name',
        '__application_command_type__': 'type',
        '__application_command_parent__': 'parent',
        '__application_command_group_command__': 'group_command',
    }

    async def callback(self, response: SlashCommandResponse[Any]) -> None:
        """|coro|

        The callback associated with this slash command.

        This can be overriden by subclasses.

        Parameters
        -----------
        response: :class:`SlashCommandResponse`
            The response of the slash command used.
        """
        pass

    @_application_command_special_method
    async def command_check(self, response: SlashCommandResponse[Any]) -> bool:
        """|coro|

        A callback that is called when the slash command is used that checks
        whether the command's callback should be called.

        The default implementation of this returns ``True``.

        .. note::

            If an exception occurs within the body then the check is considered
            a failure and :meth:`on_error`, `:meth:`Client.on_application_command_error`
            and :meth:`Cog.cog_application_command_error` (if applicable) is called.

        Parameters
        -----------
        response: :class:`SlashCommandResponse`
            The response of the slash command used.

        Returns
        ---------
        :class:`bool`
            Whether the command's callback should be called.
        """
        return True

    @_application_command_special_method
    async def on_error(self, response: SlashCommandResponse[Any], error: Exception) -> None:
        """|coro|

        A callback that is called when a slash command's callback or :meth:`command_check`
        fails with an error.

        The default implementation does nothing.

        Parameters
        -----------
        error: :class:`Exception`
            The exception that was raised.
        response: :class:`SlashCommandResponse`
            The response of the slash command used.
        """
        pass

    @classmethod
    def set_description(cls, description: str) -> None:
        """Sets the description of the slash command.

        Parameters
        -----------
        description: :class:`str`
            The description of the slash command.
        """
        cls.__application_command_description__: str = str(description)

    @classmethod
    def add_subcommand(cls, subcommand: SlashCommand) -> None:
        """Adds a subcommand to the slash command.

        Parameters
        -----------
        subcommand: :class:`SlashCommand`
            The subcommand to add.
        """
        if not isinstance(subcommand, SlashCommand):
            raise TypeError(f'subcommand must be a SlashCommand not {subcommand.__class__.__name__}')

        cls.__application_command_subcommands__[subcommand.__application_command_name__] = subcommand

    def set_parent(self, parent: SlashCommand) -> None:
        """Sets the parent of the slash command.

        Parameters
        -----------
        parent: :class:`SlashCommand`
            The slash command to set as the parent.
        """
        if not isinstance(parent, SlashCommand):
            raise TypeError(f'parent must be a SlashCommand not {parent.__class__.__name__}')

        parent.__application_command_subcommands__[self.__application_command_name__] = self
        self.__application_command_parent__: SlashCommand = parent

    @classmethod
    def add_option(cls, option: ApplicationCommandOption[Union[str, int, float]]) -> None:
        """Adds an option to the slash command.

        Parameters
        -----------
        option: :class:`ApplicationCommandOption`
            The option to add.
        """
        if not isinstance(option, ApplicationCommandOption):
            raise TypeError(f'option must be an ApplicationCommandOption not {option.__class__.__name__}')

        cls.__application_command_options__[option.name] = option

    @classmethod
    def remove_option(cls, name: str) -> Optional[ApplicationCommandOption[Union[str, int, float]]]:
        """Removes an option from the slash command by name.

        Parameters
        -----------
        name: :class:`str`
            The name of the option.

        Returns
        -----------
        Optional[:class:`ApplicationCommandOption`]
            The option that was removed. If the name is not valid then
            ``None`` is returned instead.
        """
        return cls.__application_command_options__.pop(name, None)

class MessageCommand(BaseApplicationCommand, type=ApplicationCommandType.message):
    """Represents a Discord message command.

    .. versionadded:: 2.0
    """

    async def callback(self, response: MessageCommandResponse[Any]) -> None:
        """|coro|

        The callback associated with this message command.

        This can be overriden by subclasses.

        Parameters
        -----------
        response: :class:`MessageCommandResponse`
            The response of the message command used.
        """
        pass

    @_application_command_special_method
    async def command_check(self, response: MessageCommandResponse[Any]) -> bool:
        """|coro|

        A callback that is called when the message command is used that checks
        whether the command's callback should be called.

        The default implementation of this returns ``True``.

        .. note::

            If an exception occurs within the body then the check is considered
            a failure and :meth:`on_error`, `:meth:`Client.on_application_command_error`
            and :meth:`Cog.cog_application_command_error` (if applicable) is called.

        Parameters
        -----------
        response: :class:`MessageCommandResponse`
            The response of the message command used.

        Returns
        ---------
        :class:`bool`
            Whether the command's callback should be called.
        """
        return True

    @_application_command_special_method
    async def on_error(self, response: MessageCommandResponse[Any], error: Exception) -> None:
        """|coro|

        A callback that is called when a message command's callback or :meth:`command_check`
        fails with an error.

        The default implementation does nothing.

        Parameters
        -----------
        error: :class:`Exception`
            The exception that was raised.
        response: :class:`MessageCommandResponse`
            The response of the message command used.
        """
        pass


class UserCommand(BaseApplicationCommand, type=ApplicationCommandType.user):
    """Represents a Discord user command.

    .. versionadded:: 2.0
    """

    async def callback(self, response: UserCommandResponse[Any]) -> None:
        """|coro|

        The callback associated with this user command.

        This can be overriden by subclasses.

        Parameters
        -----------
        response: :class:`UserCommandResponse`
            The response of the user command used.
        """
        pass

    @_application_command_special_method
    async def command_check(self, response: UserCommandResponse[Any]) -> bool:
        """|coro|

        A callback that is called when the user command is used that checks
        whether the command's callback should be called.

        The default implementation of this returns ``True``.

        .. note::

            If an exception occurs within the body then the check is considered
            a failure and :meth:`on_error`, `:meth:`Client.on_application_command_error`
            and :meth:`Cog.cog_application_command_error` (if applicable) is called.

        Parameters
        -----------
        response: :class:`UserCommandResponse`
            The response of the user command used.

        Returns
        ---------
        :class:`bool`
            Whether the command's callback should be called.
        """
        return True

    @_application_command_special_method
    async def on_error(self, response: UserCommandResponse[Any], error: Exception) -> None:
        """|coro|

        A callback that is called when a user command's callback or :meth:`command_check`
        fails with an error.

        The default implementation does nothing.

        Parameters
        -----------
        error: :class:`Exception`
            The exception that was raised.
        response: :class:`UserCommandResponse`
            The response of the user command used.
        """
        pass
