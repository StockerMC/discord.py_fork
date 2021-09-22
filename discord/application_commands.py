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
from typing import TYPE_CHECKING, Type, Any, Dict, TypeVar, List, Optional, Union, ClassVar, Tuple, Iterator, Callable

from operator import attrgetter
from .enums import ApplicationCommandType, ApplicationCommandOptionType, InteractionType
from .utils import resolve_annotation, MISSING, _get_as_snowflake, copy_doc
from .member import Member
from .user import User
from .role import Role
from .message import Message
from .interactions import Interaction, InteractionResponse
from .object import Object
from .channel import TextChannel, StageChannel, VoiceChannel, CategoryChannel, StoreChannel, Thread, PartialMessageable

if TYPE_CHECKING:
    from .types.interactions import (
        ApplicationCommand as ApplicationCommandPayload,
        ApplicationCommandOptionChoice as ApplicationCommandOptionChoicePayload,
        ApplicationCommandOption as ApplicationCommandOptionPayload,
        InteractionData,
        ApplicationCommandInteractionDataResolved,
        ApplicationCommandInteractionData
    )

    from .state import ConnectionState
    from .guild import Guild
    from .webhook import Webhook
    from .permissions import Permissions
    from .client import Client

    T = TypeVar('T')
    ValidOptionTypes = Union[
        Type[str],
        Type[int],
        Type[float],
        Type[Member],
        Type[User],
        Type[Role],
        Type[TextChannel],
        Type[StageChannel],
        Type[VoiceChannel],
        Type[CategoryChannel]
    ]
    ACOT = TypeVar('ACOT', bound=Union[ApplicationCommandOptionType, ValidOptionTypes])
    ApplicationCommandKey = Tuple[str, int, Optional['ApplicationCommandKey']]  # name, type, parent
    InteractionChannel = Union[
        VoiceChannel, StageChannel, TextChannel, CategoryChannel, StoreChannel, Thread, PartialMessageable
    ]

__all__ = (
    'SlashCommand',
    'MessageCommand',
    'UserCommand',
    'SlashCommandResponse',
    'MessageCommandResponse',
    'UserCommandResponse',
    'ApplicationCommandOptionChoice',
    'application_command_option',
)


OPTION_TYPE_MAPPING: Dict[Union[ValidOptionTypes], ApplicationCommandOptionType] = {
    str: ApplicationCommandOptionType.STRING,
    int: ApplicationCommandOptionType.INTEGER,
    float: ApplicationCommandOptionType.NUMBER,
    bool: ApplicationCommandOptionType.BOOLEAN,
    User: ApplicationCommandOptionType.USER,
    Member: ApplicationCommandOptionType.USER,
    Role: ApplicationCommandOptionType.ROLE,
}

for channel_type in [TextChannel, StageChannel, VoiceChannel, CategoryChannel]:
    OPTION_TYPE_MAPPING[channel_type] = ApplicationCommandOptionType.CHANNEL

def _resolve_option_type(option: Union[ValidOptionTypes, ApplicationCommandOptionType]) -> ApplicationCommandOptionType:
    if isinstance(option, ApplicationCommandOptionType):
        return option

    resolved_type = OPTION_TYPE_MAPPING.get(option)
    if resolved_type is None:
        raise TypeError(f'{option!r} is an invalid option type.')

    return resolved_type

def _get_subcommands_from_data(options: List[ApplicationCommandOptionPayload]) -> Iterator[Tuple[str, Optional[str], int]]:
    previous = None
    while options:
        option = options.pop(0)
        if 'options' in option:
            options.extend(option['options'])

        if option['type'] in (1, 2):
            yield option['name'], previous, option['type']
            previous = option['name']


class ApplicationCommandOptionChoice:
    def __init__(self, *, name: str, value: Union[str, int]) -> None:
        self.name: str = name
        self.value: Union[str, int] = value

    def to_dict(self) -> ApplicationCommandOptionChoicePayload:
        return {
            'name': self.name,
            'value': self.value
        }

# TODO make ApplicationCommandOption and ApplicationCommandInteractionOption generic for their option type?

class ApplicationCommandOption:
    __slots__= (
        'type',
        'name',
        'description',
        'required',
        'choices',
        'options',
    )

    def __init__(
        self,
        *,
        type: ApplicationCommandOptionType,
        name: str,
        description: str,
        required: bool = MISSING,
        choices: Optional[List[ApplicationCommandOptionChoice]] = None,
        options: Optional[List[ApplicationCommandOption]] = None
    ) -> None:
        self.type: ApplicationCommandOptionType = type
        self.name: str = name
        self.description: str = description
        self.required: bool = required
        self.choices: Optional[List[ApplicationCommandOptionChoice]] = choices
        self.options: Optional[List[ApplicationCommandOption]] = options

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} type={self.type!r} name={self.name!r} description={self.description!r} required={self.required!r}>'

    def to_dict(self) -> ApplicationCommandOptionPayload:
        if self.type is MISSING:
            raise TypeError(f'the type of the option {self.name!r} must be set')

        ret: ApplicationCommandOptionPayload = {
            'type': int(self.type),  # type: ignore
            'name': self.name,
            'description': self.description,
        }

        if self.required is not MISSING:
            ret['required'] = self.required

        if self.choices is not None:
            ret['choices'] = [choice.to_dict() for choice in self.choices]

        if self.options is not None:
            ret['options'] = [option.to_dict() for option in self.options]

        return ret


def application_command_option(
    *,
    description: str,
    name: str = MISSING,
    type: ApplicationCommandOptionType = MISSING,
    required: bool = True,
    choices: Optional[List[ApplicationCommandOptionChoice]] = None,
) -> Any:
    """

    """
    if type is not MISSING:
        resolved_type = _resolve_option_type(type)
    else:
        resolved_type = MISSING

    if choices is not None:
        for choice in choices:
            if not isinstance(choice, ApplicationCommandOptionChoice):
                raise TypeError(f'choices must only contain ApplicationCommandOptionChoice instances, not {choice.__class__.__name__}')

    return ApplicationCommandOption(
        name=name,
        description=description,
        type=resolved_type,
        required=required,
        choices=choices,
    )

def _get_options(
    attr_namespace: Dict[str, Any],
    annotation_namespace: Dict[str, Any],
    globals: Dict[str, Any],
    locals: Dict[str, Any]
) -> Dict[str, ApplicationCommandOption]:
    options: Dict[str, ApplicationCommandOption] = {}
    cache: Dict[str, Any] = {}
    for attr_name, attr in attr_namespace.items():
        if not isinstance(attr, ApplicationCommandOption):
            continue

        if attr_name in annotation_namespace:
            annotation = resolve_annotation(annotation_namespace[attr_name], globals, locals, cache)

            origin = getattr(annotation, '__origin__', None)

            if origin is Union:
                args = list(annotation.__args__)
                if len(args) > 2:
                    raise TypeError("Union typehint can't have more than 2 types.")

                try:
                    args.remove(type(None))
                except ValueError:
                    raise TypeError('None must be a type in a Union typehint.') from None
                else:
                    attr.required = False

                annotation = args[0]

            resolved_option_type = _resolve_option_type(annotation)

            if attr.type is MISSING:
                attr.type = resolved_option_type

        if attr.name is MISSING:
            attr.name = attr_name

        options[attr_name] = attr

    return options


class SlashCommandOptions:
    def __init__(
        self,
        *,
        guild_id: Optional[int],
        options: Optional[List[ApplicationCommandOptionPayload]],
        resolved_data: Optional[ApplicationCommandInteractionDataResolved],
        state: ConnectionState,
        optional_options: List[str],
    ) -> None:
        self.__optional_options__: List[str] = optional_options
        if options is None:
            return

        options = options[:]  # so we don't modify the original list

        while options:
            option = options.pop(0)
            nested_options = option.get('options')
            if nested_options is not None:
                options.extend(nested_options)
                continue

            value = option.get('value')
            if option['type'] == 6:  # user
                resolved_user = resolved_data['users'][value]  # type: ignore
                if guild_id is not None:
                    guild = state._get_guild(guild_id) or Object(id=guild_id)
                    member_with_user = {**resolved_data['members'][value], 'user': resolved_user}  # type: ignore
                    value = Member(state=state, data=member_with_user, guild=guild)  # type: ignore
                else:
                    value = User(state=state, data=resolved_user, guild=guild)  # type: ignore
            elif option['type'] == 7:  # channel
                resolved_channel = resolved_data['channels'][value]  # type: ignore
                if guild_id is not None:
                    guild = state._get_guild(guild_id) or Object(id=guild_id)
                    value = TextChannel(state=state, guild=guild, data=resolved_channel)  # type: ignore
            elif option['type'] == 7:  # channel
                resolved_channel = resolved_data['channels'][value]  # type: ignore
                if guild_id is not None:
                    guild = state._get_guild(guild_id)
                    if guild is not None:
                        value = guild._resolve_channel(int(resolved_channel['id']))  # there isn't enough data in the resolved channels from the payload
            elif option['type'] == 9:  # mention (role or user)
                if guild_id is not None:
                    guild = state._get_guild(guild_id) or Object(id=guild_id)
                    try:
                        value = Member(state=state, data=resolved_data['members'][value], guild=guild)  # type: ignore
                    except KeyError:
                        value = Role(guild=guild, state=state, data=resolved_data['roles'][value]) # type: ignore
                else:
                    value = User(state=state, data=resolved_data['users'][value])  # type: ignore

            setattr(self, option['name'], value)

    def __getattr__(self, name: str) -> Any:
        if name in self.__optional_options__:
            return None

        raise AttributeError(name)


def _get_used_subcommand(options: Union[ApplicationCommandPayload, ApplicationCommandOptionPayload]) -> Optional[str]:
    subcommands = options.get('options', [options])
    while subcommands:
        subcommand = subcommands.pop(0)
        if subcommand['type'] == 1:
            return subcommand['name']

        if subcommand['type'] == 2:
            return _get_used_subcommand(subcommand)

        return None

    return None


# def _recursively_set_subcommand_instance(subcommand_instance: BaseApplicationCommand) -> None:
    # parent = subcommand_instance.__application_command_parent__
    # while parent is not None:
    #     subcommand = parent.__application_command_subcommands__[subcommand_instance.__application_command_name__]
    #     parent.__application_command_subcommands__[subcommand_instance.__application_command_name__] = subcommand_instance
    #     parent = subcommand.__application_command_parent__


# original function is flatten_user in member.py
def flatten(original_cls: Type[Any], original_attr: str) -> Callable[[Type[BaseApplicationCommandResponse]], Type[BaseApplicationCommandResponse]]:
    def decorator(cls: Type[BaseApplicationCommandResponse]) -> Type[BaseApplicationCommandResponse]:
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
                setattr(cls, attr, property(getter, doc=f'Equivalent to :attr:`{original_cls}.{attr}`'))
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
class BaseApplicationCommandResponse:
    """
    
    """
    if TYPE_CHECKING:
        command: BaseApplicationCommand
        # interaction attributes
        id: int
        type: InteractionType
        data: Optional[InteractionData]
        token: str
        version: int
        channel_id: Optional[int]
        guild_id: Optional[int]
        application_id: int
        message: Optional[Message]
        user: Optional[Union[User, Member]]
        _permissions: int
        # properties
        guild: Guild
        channel: Optional[InteractionChannel]
        permissions: Permissions
        response: InteractionResponse
        followup: Webhook
        # interaction/interaction response methods
        original_message = Interaction.original_message
        edit_original_message = Interaction.edit_original_message
        delete_original_message = Interaction.delete_original_message
        is_done = InteractionResponse.is_done
        defer = InteractionResponse.defer
        pong = InteractionResponse.pong
        send_message = InteractionResponse.send_message
        edit_message = InteractionResponse.edit_message

    def __init__(self, interaction: Interaction) -> None:
        self.interaction: Interaction = interaction


class SlashCommandResponse(BaseApplicationCommandResponse):
    """
    
    """
    def __init__(self, interaction: Interaction, options: SlashCommandOptions, command: SlashCommand) -> None:
        super().__init__(interaction)
        self.options: Any = options  # we typehint it as `Any` to avoid type checker errors when accessing attributes
        self.command: SlashCommand = command


class MessageCommandResponse(BaseApplicationCommandResponse):
    """
    
    """
    def __init__(self, interaction: Interaction, target: Message, command: MessageCommand) -> None:
        super().__init__(interaction)
        self.target: Message = target
        self.command: MessageCommand = command


class UserCommandResponse(BaseApplicationCommandResponse):
    """
    
    """
    def __init__(self, interaction: Interaction, target: Union[Member, User], command: UserCommand) -> None:
        super().__init__(interaction)
        self.target: Union[Member, User] = target
        self.command: UserCommand = command


# TODO make sure global/guild specific commands work

def _traverse_mro_for_attr(cls: Type[object], attr_name: str, default: T = MISSING) -> Union[Any, T]:
    attr = default
    for base in cls.__mro__[:-1]:
        attr = getattr(base, attr_name, default)  # type: ignore
        if attr is default:
            continue

        break

    return attr


class BaseApplicationCommand:
    if TYPE_CHECKING:
        __application_command_options__: ClassVar[Dict[str, ApplicationCommandOption]]
        __application_command_name__: ClassVar[str]
        __application_command_description__: ClassVar[str]
        __application_command_type__: ClassVar[ApplicationCommandType]
        __application_command_parent__: Union[Type[BaseApplicationCommand], BaseApplicationCommand]
        __application_command_default_permission__: ClassVar[bool]
        __application_command_guild_ids__: ClassVar[List[int]]
        __application_command_global_command__: ClassVar[bool]
        __application_command_group_command__: ClassVar[bool]
        __application_command_subcommands__: ClassVar[Dict[str, Union[BaseApplicationCommand]]]

    __discord_application_command__: ClassVar[bool] = True

    __application_command_repr_attrs__: Dict[str, str] = {  # actual key: key to display
        '__application_command_name__': 'name',
        '__application_command_type__': 'type',
    }

    __slots__ = (
        '__application_command_options__',
        '__application_command_name__',
        '__application_command_description__',
        '__application_command_type__',
        '__application_command_parent__',
        '__application_command_default_permission__',
        '__application_command_guild_ids__',
        '__application_command_global_command__',
        '__application_command_subcommands__',
    )

    def __init_subclass__(
        cls: Type[BaseApplicationCommand],
        *,
        name: Optional[str] = None,
        description: str = MISSING,
        parent: Optional[Type[BaseApplicationCommand]] = None,  # make this SlashCommand?
        command_type: ApplicationCommandType = MISSING,
        default_permission: bool = True,
        guild_ids: List[int] = [],
        global_command: bool = MISSING,
        group: bool = False,
    ) -> None:
        if command_type is MISSING:
            command_type = _traverse_mro_for_attr(cls, '__application_command_type__')

        if name is None:
            name = cls.__name__

        # NOTE: should we be doing this?
        if command_type is ApplicationCommandType.SLASH:
            name = name.lower()

        if description is MISSING:
            doc = _traverse_mro_for_attr(cls, '__doc__', None)
            if doc is None:
                description = MISSING
            else:
                description = inspect.cleandoc(doc)

        if parent is not None:
            if parent.__application_command_type__ is not ApplicationCommandType.SLASH:
                raise TypeError(f'parent must derive from SlashCommand not {parent.__name__}')

            if command_type is not ApplicationCommandType.SLASH:
                raise TypeError('only slash commands can have parents')

        if command_type is not MISSING and not isinstance(command_type, ApplicationCommandType):
            raise TypeError(f'command_type must be an ApplicationCommandType member not {command_type.__class__.__name__}') # is member the right word here

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

        cls_dict = dict(cls.__dict__)
        attrs_to_remove = ['__module__', '__doc__', '__annotations__']
        for attr in attrs_to_remove:
            cls_dict.pop(attr, None)

        options = _get_options(cls_dict, cls.__annotations__, global_ns, local_ns)

        cls.__application_command_options__ = options
        cls.__application_command_name__ = str(name)

        cls.__application_command_description__ = str(description)
        # it gets set as an instance later
        cls.__application_command_parent__ = parent  # type: ignore
        cls.__application_command_type__ = command_type
        cls.__application_command_default_permission__ = bool(default_permission)
        cls.__application_command_guild_ids__ = guild_ids
        if global_command is MISSING:
            global_command = False if guild_ids else True

        cls.__application_command_global_command__ = global_command
        cls.__application_command_group_command__ = group
        cls.__application_command_subcommands__ = {}

        if parent is not None:
            # it gets set as an instance later
            parent.__application_command_subcommands__[name] = cls  # type: ignore

    def __repr__(self) -> str:
        attrs = ' '.join([f'{display_key}={getattr(self, key)!r}' for key, display_key in self.__application_command_repr_attrs__.items()])
        return f'<{self.__class__.__name__} {attrs}>'

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
        while subcommands:
            subcommand = subcommands.pop(0)
            if subcommand.__application_command_name__ == name:
                return subcommand

            if name in subcommand.__application_command_subcommands__:
                return subcommand.__application_command_subcommands__[name]

        return None

    def _verify_data(self, application_command_data: ApplicationCommandInteractionData, guild_id: Optional[int]) -> Optional[BaseApplicationCommand]:
        if not self.__application_command_global_command__ and guild_id is not None and guild_id not in self.__application_command_guild_ids__:
            return None

        options = application_command_data.get('options')
        used_subcommand = None
        if self.__application_command_parent__ or self.__application_command_subcommands__ and options:
            used_subcommand = _get_used_subcommand(application_command_data)  # type: ignore

        if used_subcommand is not None:
            return self._recursively_get_subcommand(used_subcommand)

        if self.__application_command_name__ != application_command_data['name'] or int(self.__application_command_type__) != application_command_data['type']:  # type: ignore
            return None

        return self

    @classmethod
    def _as_option(cls) -> ApplicationCommandOption:
        type = ApplicationCommandOptionType.SUB_COMMAND_GROUP if cls.__application_command_group_command__ else ApplicationCommandOptionType.SUB_COMMAND
        return ApplicationCommandOption(
            type=type,
            name=cls.__application_command_name__,
            description=cls.__application_command_description__,
            options=list(cls.__application_command_options__.values())
        )

    async def _scheduled_task(self, response: BaseApplicationCommandResponse, client: Client) -> None:
        try:
            allow = await self.command_check(response)
            if not allow:
                return

            await self.callback(response)
            if not response.response._responded:
                await response.defer()
        except Exception as e:
            client.dispatch('application_command_error', response, e)
            await self.on_error(response, e)

    @classmethod
    def set_name(cls, name: str) -> None:
        cls.__application_command_name__ = str(name)

    @classmethod
    def set_type(cls, type: ApplicationCommandType) -> None:
        cls.__application_command_type__ = type

    async def callback(self, response: BaseApplicationCommandResponse) -> None:
        """

        """
        pass

    async def command_check(self, response: BaseApplicationCommandResponse) -> bool:
        """

        """
        return True

    # make a note that says that it doesn't propogate down to subcommands
    async def on_error(self, response: BaseApplicationCommandResponse, error: BaseException) -> None:
        """
        
        """
        pass

    @classmethod
    def to_dict(cls) -> ApplicationCommandPayload:
        ret: ApplicationCommandPayload = {
            'name': cls.__application_command_name__,
            'type': int(cls.__application_command_type__),  # type: ignore
            'default_permission': cls.__application_command_default_permission__,
        }

        if cls.__application_command_type__ is ApplicationCommandType.SLASH:
            ret['description'] = cls.__application_command_description__

            extra = []
            for command in cls.__application_command_subcommands__.values():
                type = ApplicationCommandOptionType.SUB_COMMAND_GROUP if command.__application_command_group_command__ else ApplicationCommandOptionType.SUB_COMMAND
                extra.append(ApplicationCommandOption(
                    type=type,
                    name=command.__application_command_name__,
                    description=command.__application_command_description__,
                    options=[
                        *list(command.__application_command_options__.values()),
                        *[subcommand._as_option() for subcommand in command.__application_command_subcommands__.values()]
                    ],
                ))
                
            options = sorted([*cls.__application_command_options__.values(), *extra], key=lambda o: not o.required)  # required options have to come before optional options
            if options:
                options = [option.to_dict() for option in options]
                ret['options'] = options

        return ret

# TODO add examples and docstrings

class SlashCommand(BaseApplicationCommand, command_type=ApplicationCommandType.SLASH):
    """Represents a discord slash command.
    
    """
    
    __application_command_repr_attrs__: Dict[str, str] = {  # actual key: key to display
        '__application_command_name__': 'name',
        '__application_command_type__': 'type',
        '__application_command_parent__': 'parent',
        '__application_command_group_command__': 'group_command',
    }

    async def callback(self, response: SlashCommandResponse) -> None:
        pass

    async def command_check(self, response: SlashCommandResponse) -> bool:
        return True

    async def on_error(self, error: BaseException, response: SlashCommandResponse) -> None:
        pass

    @classmethod
    def set_description(cls, description: str) -> None:
        """
        
        """
        cls.__application_command_description__ = str(description)

    @classmethod
    def add_subcommand(cls, subcommand: SlashCommand) -> None:
        """
        
        """
        if not isinstance(subcommand, SlashCommand):
            raise TypeError(f'subcommand must be a SlashCommand not {subcommand.__class__.__name__}')

        cls.__application_command_parent__ = subcommand

    @classmethod
    def set_subcommand(cls, parent: SlashCommand) -> None:
        """
        
        """
        if not isinstance(parent, SlashCommand):
            raise TypeError(f'parent must be a SlashCommand not {parent.__class__.__name__}')

        cls.__application_command_parent__ = parent

    @classmethod
    def add_option(cls, option: ApplicationCommandOption) -> None:
        """
        
        """
        if not isinstance(option, ApplicationCommandOption):
            raise TypeError(f'option must be an ApplicationCommandOption not {option.__class__.__name__}')

        cls.__application_command_options__[option.name] = option

    @classmethod
    def remove_option(cls, name: str) -> Optional[ApplicationCommandOption]:
        """
        
        """
        return cls.__application_command_options__.pop(name, None)

class MessageCommand(BaseApplicationCommand, command_type=ApplicationCommandType.MESSAGE):
    """Represents a discord message command.
    
    """
    async def callback(self, response: MessageCommandResponse) -> None:
        pass

    async def command_check(self, response: MessageCommandResponse) -> bool:
        return True

    async def on_error(self, error: BaseException, response: MessageCommandResponse) -> None:
        pass


class UserCommand(BaseApplicationCommand, command_type=ApplicationCommandType.USER):
    """Represents a discord user command.
    
    """
    async def callback(self, response: UserCommandResponse) -> None:
        pass

    async def command_check(self, response: UserCommandResponse) -> bool:
        return True

    async def on_error(self, error: BaseException, response: UserCommandResponse) -> None:
        pass
