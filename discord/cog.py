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

import inspect
from .utils import MISSING
from ._types import _BaseCommand

from typing import Any, Callable, ClassVar, Dict, Generator, List, Optional, TYPE_CHECKING, Tuple, TypeVar, Type, Union

if TYPE_CHECKING:
    from .ext.commands.context import Context
    from .ext.commands.core import Command
    from .ext.commands.bot import Bot
    from .client import Client

    from .application_commands import (
        SlashCommand,
        MessageCommand,
        UserCommand,
        SlashCommandResponse,
        MessageCommandResponse,
        UserCommandResponse
    )

    ApplicationCommand = Union[
        SlashCommand,
        MessageCommand,
        UserCommand
    ]
    ApplicationCommandKey = Tuple[str, int, Optional['ApplicationCommandKey']]  # name, type, parent

__all__ = (
    'CogMeta',
    'Cog',
)

CogT = TypeVar('CogT', bound='Cog')
FuncT = TypeVar('FuncT', bound=Callable[..., Any])


class CogMeta(type):
    """A metaclass for defining a cog.

    Note that you should probably not use this directly. It is exposed
    purely for documentation purposes along with making custom metaclasses to intermix
    with other metaclasses such as the :class:`abc.ABCMeta` metaclass.

    For example, to create an abstract cog mixin class, the following would be done.

    .. code-block:: python3

        import abc

        class CogABCMeta(discord.CogMeta, abc.ABCMeta):
            pass

        class SomeMixin(metaclass=abc.ABCMeta):
            pass

        class SomeCogMixin(SomeMixin, discord.Cog, metaclass=CogABCMeta):
            pass

    .. note::

        When passing an attribute of a metaclass that is documented below, note
        that you must pass it as a keyword-only argument to the class creation
        like the following example:

        .. code-block:: python3

            class MyCog(discord.Cog, name='My Cog'):
                pass

    Attributes
    -----------
    name: :class:`str`
        The cog name. By default, it is the name of the class with no modification.
    description: :class:`str`
        The cog description. By default, it is the cleaned docstring of the class.

        .. versionadded:: 1.6

    command_attrs: :class:`dict`
        A list of attributes to apply to every command inside this cog. The dictionary
        is passed into the :class:`Command` options at ``__init__``.
        If you specify attributes inside the command attribute in the class, it will
        override the one specified inside this attribute. For example:

        .. code-block:: python3

            class MyCog(discord.Cog, command_attrs=dict(hidden=True)):
                @commands.command()
                async def foo(self, ctx):
                    pass # hidden -> True

                @commands.command(hidden=False)
                async def bar(self, ctx):
                    pass # hidden -> False
    """
    __cog_name__: str
    __cog_settings__: Dict[str, Any]
    __cog_commands__: List[Command]
    __cog_listeners__: List[Tuple[str, str]]

    def __new__(cls: Type[CogMeta], *args: Any, **kwargs: Any) -> CogMeta:
        name, bases, attrs = args
        attrs['__cog_name__'] = kwargs.pop('name', name)
        attrs['__cog_settings__'] = kwargs.pop('command_attrs', {})

        description = kwargs.pop('description', None)
        if description is None:
            description = inspect.cleandoc(attrs.get('__doc__', ''))
        attrs['__cog_description__'] = description

        commands = {}
        listeners = {}
        no_bot_cog = 'Commands or listeners must not start with cog_ or bot_ (in method {0.__name__}.{1})'

        new_cls = super().__new__(cls, name, bases, attrs, **kwargs)
        for base in reversed(new_cls.__mro__):
            for elem, value in base.__dict__.items():
                if elem in commands:
                    del commands[elem]
                if elem in listeners:
                    del listeners[elem]

                is_static_method = isinstance(value, staticmethod)
                if is_static_method:
                    value = value.__func__

                if isinstance(value, _BaseCommand):
                    if is_static_method:
                        raise TypeError(f'Command in method {base}.{elem!r} must not be staticmethod.')
                    if elem.startswith(('cog_', 'bot_')):
                        raise TypeError(no_bot_cog.format(base, elem))
                    commands[elem] = value
                elif inspect.iscoroutinefunction(value):
                    try:
                        getattr(value, '__cog_listener__')
                    except AttributeError:
                        continue
                    else:
                        if elem.startswith(('cog_', 'bot_')):
                            raise TypeError(no_bot_cog.format(base, elem))
                        listeners[elem] = value

        new_cls.__cog_commands__ = list(commands.values()) # this will be copied in Cog.__new__

        listeners_as_list = []
        for listener in listeners.values():
            for listener_name in listener.__cog_listener_names__:
                # I use __name__ instead of just storing the value so I can inject
                # the self attribute when the time comes to add them to the bot
                listeners_as_list.append((listener_name, listener.__name__))

        new_cls.__cog_listeners__ = listeners_as_list
        return new_cls

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args)

    @classmethod
    def qualified_name(cls) -> str:
        return cls.__cog_name__

def _cog_special_method(func: FuncT) -> FuncT:
    func.__cog_special_method__ = None
    return func

class Cog(metaclass=CogMeta):
    """The base class that all cogs must inherit from.

    A cog is a collection of commands, listeners, and optional state to
    help group commands together. More information on them can be found on
    the :ref:`cogs` page.

    When inheriting from this class, the options shown in :class:`CogMeta`
    are equally valid here.
    """
    __cog_name__: ClassVar[str]
    __cog_settings__: ClassVar[Dict[str, Any]]
    __cog_commands__: ClassVar[List[Command]]
    __cog_listeners__: ClassVar[List[Tuple[str, str]]]
    __cog_application_commands__: Dict[ApplicationCommandKey, ApplicationCommand] = {}

    def __new__(cls: Type[CogT], *args: Any, **kwargs: Any) -> CogT:
        # For issue 426, we need to store a copy of the command objects
        # since we modify them to inject `self` to them.
        # To do this, we need to interfere with the Cog creation process.
        self = super().__new__(cls)
        cmd_attrs = cls.__cog_settings__

        # Either update the command with the cog provided defaults or copy it.
        # r.e type ignore, type-checker complains about overriding a ClassVar
        self.__cog_commands__ = tuple(c._update_copy(cmd_attrs) for c in cls.__cog_commands__)  # type: ignore

        lookup = {
            cmd.qualified_name: cmd
            for cmd in self.__cog_commands__
        }

        # Update the Command instances dynamically as well
        for command in self.__cog_commands__:
            setattr(self, command.callback.__name__, command)
            parent = command.parent
            if parent is not None:
                # Get the latest parent reference
                parent = lookup[parent.qualified_name]  # type: ignore

                # Update our parent's reference to our self
                parent.remove_command(command.name)  # type: ignore
                parent.add_command(command)  # type: ignore

        return self

    def get_commands(self) -> List[Command]:
        r"""
        Returns
        --------
        List[:class:`.Command`]
            A :class:`list` of :class:`.Command`\s that are
            defined inside this cog.

            .. note::

                This does not include subcommands.
        """
        return [c for c in self.__cog_commands__ if c.parent is None]

    @property
    def qualified_name(self) -> str:
        """:class:`str`: Returns the cog's specified name, not the class name."""
        return self.__cog_name__

    @property
    def description(self) -> str:
        """:class:`str`: Returns the cog's description, typically the cleaned docstring."""
        return self.__cog_description__

    @description.setter
    def description(self, description: str) -> None:
        self.__cog_description__ = description

    def walk_commands(self) -> Generator[Command, None, None]:
        """An iterator that recursively walks through this cog's commands and subcommands.

        Yields
        ------
        Union[:class:`.Command`, :class:`.Group`]
            A command or group from the cog.
        """
        from .ext.commands.core import GroupMixin
        for command in self.__cog_commands__:
            if command.parent is None:
                yield command
                if isinstance(command, GroupMixin):
                    yield from command.walk_commands()

    def get_listeners(self) -> List[Tuple[str, Callable[..., Any]]]:
        """Returns a :class:`list` of (name, function) listener pairs that are defined in this cog.

        Returns
        --------
        List[Tuple[:class:`str`, :ref:`coroutine <coroutine>`]]
            The listeners defined in this cog.
        """
        return [(name, getattr(self, method_name)) for name, method_name in self.__cog_listeners__]

    @classmethod
    def _get_overridden_method(cls, method: FuncT) -> Optional[FuncT]:
        """Return None if the method is not overridden. Otherwise returns the overridden method."""
        return getattr(method.__func__, '__cog_special_method__', method)

    @classmethod
    def listener(cls, name: str = MISSING) -> Callable[[FuncT], FuncT]:
        """A decorator that marks a function as a listener.

        This is the cog equivalent of :meth:`.Bot.listen`.

        Parameters
        ------------
        name: :class:`str`
            The name of the event being listened to. If not provided, it
            defaults to the function's name.

        Raises
        --------
        TypeError
            The function is not a coroutine function or a string was not passed as
            the name.
        """

        if name is not MISSING and not isinstance(name, str):
            raise TypeError(f'Cog.listener expected str but received {name.__class__.__name__!r} instead.')

        def decorator(func: FuncT) -> FuncT:
            actual = func
            if isinstance(actual, staticmethod):
                actual = actual.__func__
            if not inspect.iscoroutinefunction(actual):
                raise TypeError('Listener function must be a coroutine function.')
            actual.__cog_listener__ = True
            to_assign = name or actual.__name__
            try:
                actual.__cog_listener_names__.append(to_assign)
            except AttributeError:
                actual.__cog_listener_names__ = [to_assign]
            # we have to return `func` instead of `actual` because
            # we need the type to be `staticmethod` for the metaclass
            # to pick it up but the metaclass unfurls the function and
            # thus the assignments need to be on the actual function
            return func
        return decorator

    def has_error_handler(self) -> bool:
        """:class:`bool`: Checks whether the cog has a command error handler.

        .. versionadded:: 1.7
        """
        return not hasattr(self.cog_command_error.__func__, '__cog_special_method__')

    def has_application_command_error_handler(self) -> bool:
        """:class:`bool`: Checks whether the cog has an application command error handler.
        
        .. versionadded:: 2.0
        """
        return not hasattr(self.cog_application_command_error.__func__, '__cog_special_method__')

    def add_application_command(self, application_command: ApplicationCommand) -> None:
        self.__cog_application_commands__[application_command._get_key()] = application_command

    def get_application_commands(self) -> List[ApplicationCommand]:
        return list(self.__cog_application_commands__.values())

    def remove_application_command(self, application_command: Union[ApplicationCommand, Type[ApplicationCommand]]) -> Optional[ApplicationCommand]:
        return self.__cog_application_commands__.pop(application_command._get_key(), None)

    @_cog_special_method
    def cog_unload(self) -> None:
        """A special method that is called when the cog gets removed.

        This function **cannot** be a coroutine. It must be a regular
        function.

        Subclasses must replace this if they want special unloading behaviour.
        """
        pass

    @_cog_special_method
    def bot_check_once(self, ctx: Context[Any]) -> bool:
        """A special method that registers as a :meth:`.Bot.check_once`
        check.

        This function **can** be a coroutine and must take a sole parameter,
        ``ctx``, to represent the :class:`.Context`.
        """
        return True

    @_cog_special_method
    def bot_check(self, ctx: Context[Any]) -> bool:
        """A special method that registers as a :meth:`.Bot.check`
        check.

        This function **can** be a coroutine and must take a sole parameter,
        ``ctx``, to represent the :class:`.Context`.
        """
        return True

    @_cog_special_method
    def cog_check(self, ctx: Context[Any]) -> bool:
        """A special method that registers as a :func:`~discord.ext.commands.check`
        for every command and subcommand in this cog.

        This function **can** be a coroutine and must take a sole parameter,
        ``ctx``, to represent the :class:`.Context`.
        """
        return True

    @_cog_special_method
    async def client_application_command_check(self, response: Union[SlashCommandResponse, MessageCommandResponse, UserCommandResponse]) -> bool:
        """A special method that registers as a :meth:`.Client.application_command_check`
        check.

        This function **must** be a coroutine and must take a sole parameter,
        ``response``, to represent the response of the application command.
        """
        return True

    @_cog_special_method
    async def cog_application_command_check(self, response: Union[SlashCommandResponse, MessageCommandResponse, UserCommandResponse]) -> bool:
        """A special method that registers as a :meth:`command_check` for every
        application command inside this cog.

        This function **must** be a coroutine and must take a sole parameter,
        ``response``, to represent the response of the application command.
        """
        return True

    @_cog_special_method
    async def cog_command_error(self, ctx: Context[Any], error: Exception) -> None:
        """A special method that is called whenever an error
        is dispatched in a command inside this cog.

        This is similar to :func:`.on_command_error` except only applying
        to the commands inside this cog.

        This **must** be a coroutine.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context where the error happened.
        error: :class:`CommandError`
            The error that happened.
        """
        pass

    @_cog_special_method
    async def cog_application_command_error(self, response: Union[SlashCommandResponse, MessageCommandResponse, UserCommandResponse], error: Exception) -> None:
        """A special method that is called whenever an error
        is dispatched inside an application command inside this cog.

        This is similar to :func:`.on_application_command_error` except only applying
        to the application commands inside this cog.

        This **must** be a coroutine.

        Parameters
        -----------
        response: Union[:class:`SlashCommandResponse`, :class:`MessageCommandResponse`, :class:`UserCommandResponse`]
            The response for the application command.
        error: :class:`Exception`
            The error that was raised.
        """
        pass

    @_cog_special_method
    async def cog_before_invoke(self, ctx: Context[Any]) -> None:
        """A special method that acts as a cog local pre-invoke hook.

        This is similar to :meth:`.Command.before_invoke`.

        This **must** be a coroutine.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context.
        """
        pass

    @_cog_special_method
    async def cog_after_invoke(self, ctx: Context[Any]) -> None:
        """A special method that acts as a cog local post-invoke hook.

        This is similar to :meth:`.Command.after_invoke`.

        This **must** be a coroutine.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context.
        """
        pass

    def _inject(self: CogT, client: Union[Client, Bot]) -> CogT:
        cls = self.__class__
        client_no_commands = "Client doesn't support ext.commands commands."

        # circular import
        from .ext.commands.bot import Bot

        # realistically, the only thing that can cause loading errors
        # is essentially just the command loading, which raises if there are
        # duplicates. When this condition is met, we want to undo all what
        # we've added so far for some form of atomic loading.
        for index, command in enumerate(self.__cog_commands__):
            if not isinstance(client, Bot):
                raise TypeError(client_no_commands)

            command.cog = self
            if command.parent is None:
                try:
                    client.add_command(command)
                except Exception as e:
                    # undo our additions
                    for to_undo in self.__cog_commands__[:index]:
                        if to_undo.parent is None:
                            client.remove_command(to_undo.name)
                    raise e

        # check if we're overriding the default
        if cls.bot_check is not Cog.bot_check:
            if not isinstance(client, Bot):
                raise TypeError(client_no_commands)

            client.add_check(self.bot_check)

        if cls.bot_check_once is not Cog.bot_check_once:
            if not isinstance(client, Bot):
                raise TypeError(client_no_commands)

            client.add_check(self.bot_check_once, call_once=True)

        if cls.client_application_command_check is not Cog.client_application_command_check:
            client.add_application_command_check(self.client_application_command_check)

        # while Bot.add_listener can raise if it's not a coroutine,
        # this precondition is already met by the listener decorator
        # already, thus this should never raise.
        # Outside of, memory errors and the like...
        for name, method_name in self.__cog_listeners__:
            client.add_listener(getattr(self, method_name), name)

        for command in self.__cog_application_commands__.values():
            command._cog = self
            client.add_application_command(command)  # type: ignore

        return self

    def _eject(self, client: Union[Client, Bot]) -> None:
        cls = self.__class__

        # circular import
        from .ext.commands.bot import Bot

        try:
            client_no_commands = "Client doesn't support ext.commands commands."
            application_commands = self.__cog_application_commands__

            if isinstance(client, Bot):
                for command in self.__cog_commands__:
                    if command.parent is None:
                        client.remove_command(command.name)

            for _, method_name in self.__cog_listeners__:
                client.remove_listener(getattr(self, method_name))

            if cls.bot_check is not Cog.bot_check:
                if not isinstance(client, Bot):
                    raise TypeError(client_no_commands)

                client.remove_check(self.bot_check)

            if cls.bot_check_once is not Cog.bot_check_once:
                if not isinstance(client, Bot):
                    raise TypeError(client_no_commands)

                client.remove_check(self.bot_check_once, call_once=True)

            for command in application_commands.values():
                client.remove_application_command(command)
        finally:
            try:
                self.cog_unload()
            except Exception:
                pass
