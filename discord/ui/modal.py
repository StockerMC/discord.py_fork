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

from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    List,
    Optional,
    Dict,
    Tuple,
    Callable,
    Sequence,
)

import asyncio
import os
import sys
import time
import traceback

from functools import partial
from itertools import groupby
from .view import _component_factory, _component_to_item, _walk_all_components
from ..utils import MISSING

__all__ = (
    'Modal',
)

if TYPE_CHECKING:
    from .item import Item
    from ..components import Component
    from ..interactions import Interaction
    from ..state import ConnectionState
    from ..types.interactions import ModalInteractionData
    from ..types.components import InputText as InputTextPayload

class _ModalWeights:
    __slots__ = (
        'weights',
    )

    def __init__(self, children: List[Item[Any]]):
        self.weights: List[int] = [0, 0, 0, 0, 0]

        key = lambda i: sys.maxsize if i.row is None else i.row
        children = sorted(children, key=key)
        for _, group in groupby(children, key=key):
            for item in group:
                self.add_item(item)

    def find_open_space(self, item: Item[Any]) -> int:
        for index, weight in enumerate(self.weights):
            if weight + item.width <= 5:
                return index

        raise ValueError('could not find open space for item')

    def add_item(self, item: Item[Any]) -> None:
        if item.row is not None:
            total = self.weights[item.row] + item.width
            if total > 5:
                raise ValueError(f'item would not fit at row {item.row} ({total} > 5 width)')
            self.weights[item.row] = total
            item._rendered_row = item.row
        else:
            index = self.find_open_space(item)
            self.weights[index] += item.width
            item._rendered_row = index

    def remove_item(self, item: Item[Any]) -> None:
        if item._rendered_row is not None:
            self.weights[item._rendered_row] -= item.width
            item._rendered_row = None

    def clear(self) -> None:
        self.weights = [0, 0, 0, 0, 0]

class Modal:
    """Represents a UI modal.

    This implements similar functionality to :class:`discord.ui.View`.

    .. note::

        A modal must have at least one child.

    Parameters
    ----------
    timeout: Optional[:class:`float`]
        Timeout in seconds from last interaction with the UI before no longer accepting input.
        If ``None`` then there is no timeout.
    children: List[:class:`Item`]
        The children of the modal.
        A modal can have a maximum of 5 children.
    title: Optional[:class:`str`]
        The title of the modal, if any.
    custom_id: :class:`str`
        The ID of the modal that gets received during an interaction.
        If not given then one is generated for you.
    """

    __discord_ui_modal__: ClassVar[bool] = True

    def __init__(
        self,
        *,
        title: str,
        timeout: Optional[float] = 180,
        custom_id: str = MISSING,
        children: List[Item[Any]] = MISSING,
    ) -> None:
        self.title: str = title
        self.children: List[Item[Any]] = children
        self.custom_id: str = os.urandom(16).hex() if custom_id is MISSING else custom_id
        self.timeout: Optional[float] = timeout
        self.id: str = os.urandom(16).hex()
        self._provided_custom_id: bool = custom_id is not MISSING
        self.__weights = _ModalWeights(self.children)
        self.__cancel_callback: Optional[Callable[[], None]] = None
        self.__timeout_expiry: Optional[float] = None
        self.__timeout_task: Optional[asyncio.Task[None]] = None
        loop = asyncio.get_running_loop()
        self.__stopped: asyncio.Future[bool] = loop.create_future()

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} title={self.title!r} timeout={self.timeout} children={len(self.children)}>'

    async def __timeout_task_impl(self) -> None:
        while True:
            # Guard just in case someone changes the value of the timeout at runtime
            if self.timeout is None:
                return

            if self.__timeout_expiry is None:
                return self._dispatch_timeout()

            # Check if we've elapsed our currently set timeout
            now = time.monotonic()
            if now >= self.__timeout_expiry:
                return self._dispatch_timeout()

            # Wait N seconds to see if timeout data has been refreshed
            await asyncio.sleep(self.__timeout_expiry - now)

    def to_components(self) -> List[InputTextPayload]:
        def key(item: Item[Any]) -> int:
            return item._rendered_row or 0

        children = sorted(self.children, key=key)
        components = []
        for _, group in groupby(children, key=key):
            children = [item.to_component_dict() for item in group]
            if not children:
                continue

            components.append(
                {
                    'type': 1,
                    'components': children,
                }
            )

        return components

    @property
    def _expires_at(self) -> Optional[float]:
        if self.timeout:
            return time.monotonic() + self.timeout
        return None

    def add_item(self, item: Item[Any]) -> None:
        """Adds an item to the modal.

        Parameters
        -----------
        item: :class:`Item`
            The item to add to the modal.

        Raises
        --------
        TypeError
            An :class:`Item` was not passed.
        ValueError
            Maximum number of children has been exceeded (5)
            or the row the item is trying to be added to is full.
        """

        if len(self.children) > 5:
            raise ValueError('maximum number of children exceeded')

        if not isinstance(item, Item):
            raise TypeError(f'expected Item not {item.__class__!r}')

        self.__weights.add_item(item)
        self.children.append(item)

    def remove_item(self, item: Item[Any]) -> None:
        """Removes an item from the nidak.

        Parameters
        -----------
        item: :class:`Item`
            The item to remove from the modal.
        """

        try:
            self.children.remove(item)
        except ValueError:
            pass
        else:
            self.__weights.remove_item(item)

    def clear_items(self) -> None:
        """Removes all items from the modal."""
        self.children.clear()
        self.__weights.clear()

    async def interaction_check(self, interaction: Interaction[Any]) -> bool:
        """|coro|

        A callback that is called when a modal is submitted that checks whether
        the modal's callback should be called.

        This is useful to override if, for example, you want to ensure that the
        interaction author is a given user.

        The default implementation of this returns ``True``.

        .. note::

            If an exception occurs within the body then the check
            is considered a failure and :meth:`on_error` is called.

        Parameters
        -----------
        interaction: :class:`~discord.Interaction`
            The interaction that occurred.

        Returns
        ---------
        :class:`bool`
            Whether the modal's callback should be called.
        """
        return True

    async def on_timeout(self) -> None:
        """|coro|

        A callback that is called when a modal's timeout elapses without being explicitly stopped.
        """
        pass

    # !!!!!!!!!
    async def on_error(self, error: Exception, interaction: Interaction[Any]) -> None:
        """|coro|

        A callback that is called when the modal's callback or :meth:`interaction_check`
        fails with an error.

        The default implementation prints the traceback to stderr.

        Parameters
        -----------
        error: :class:`Exception`
            The exception that was raised.
        interaction: :class:`~discord.Interaction`
            The interaction that led to the failure.
        """
        print(f'Ignoring exception in modal {self}:', file=sys.stderr)
        traceback.print_exception(error.__class__, error, error.__traceback__, file=sys.stderr)

    async def _scheduled_task(self, interaction: Interaction[Any]) -> None:
        try:
            if self.timeout:
                self.__timeout_expiry = time.monotonic() + self.timeout

            allow = await self.interaction_check(interaction)
            if not allow:
                return

            await self.callback(interaction)
            if not interaction.response._responded:
                await interaction.response.defer()
        except Exception as e:
            return await self.on_error(e, interaction)

    def _start_listening_from_store(self, store: ModalStore, user_id: int) -> None:
        self.__cancel_callback = partial(store.remove_modal, self, user_id)
        if self.timeout:
            loop = asyncio.get_running_loop()
            if self.__timeout_task is not None:
                self.__timeout_task.cancel()

            self.__timeout_expiry = time.monotonic() + self.timeout
            self.__timeout_task = loop.create_task(self.__timeout_task_impl())

    def _dispatch(self, interaction: Interaction[Any]) -> None:
        if self.__stopped.done():
            return

        asyncio.create_task(self._scheduled_task(interaction), name=f'discord-ui-modal-dispatch-{self.id}')

    def _dispatch_timeout(self) -> None:
        if self.__stopped.done():
            return

        self.__stopped.set_result(True)
        asyncio.create_task(self.on_timeout(), name=f'discord-ui-modal-timeout-{self.id}')

    def stop(self) -> None:
        """Stops listening to interaction events from this view.

        This operation cannot be undone.
        """
        if not self.__stopped.done():
            self.__stopped.set_result(False)

        self.__timeout_expiry = None
        if self.__timeout_task is not None:
            self.__timeout_task.cancel()
            self.__timeout_task = None

        if self.__cancel_callback:
            self.__cancel_callback()
            self.__cancel_callback = None

    def is_finished(self) -> bool:
        """:class:`bool`: Whether the view has finished interacting."""
        return self.__stopped.done()

    def is_dispatching(self) -> bool:
        """:class:`bool`: Whether the view has been added for dispatching purposes."""
        return self.__cancel_callback is not None

    def is_persistent(self) -> bool:
        """:class:`bool`: Whether the modal is set up as persistent.

        A persistent modal has a set ``custom_id``, along with all of their components having
        a set ``custom_id`` as well. It also has a :attr:`timeout` set to ``None``.
        """
        return self.timeout is None and self._provided_custom_id and all(item.is_persistent() for item in self.children)

    async def wait(self) -> bool:
        """Waits until the view has finished interacting.

        A view is considered finished when :meth:`stop` is called
        or it times out.

        Returns
        --------
        :class:`bool`
            If ``True``, then the view timed out. If ``False`` then
            the view finished normally.
        """
        return await self.__stopped

    async def callback(self, interaction: Interaction[Any]) -> None:
        """|coro|

        The callback associated with this UI modal when it is submitted.

        This can be overriden by subclasses.

        Parameters
        -----------
        interaction: :class:`.Interaction`
            The interaction that triggered this UI modal.
        """
        pass

    def to_callback_data(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'custom_id': self.custom_id,
            'components': self.to_components()
        }

    def refresh(self, components: List[Component]) -> None:
        old_state: Dict[Tuple[int, str], Item] = {
            (item.type.value, item.custom_id): item  # type: ignore
            for item in self.children
        }
        children: List[Item] = []
        for component in _walk_all_components(components):
            try:
                older = old_state[(component.type.value, component.custom_id)]  # type: ignore
            except (KeyError, AttributeError):
                children.append(_component_to_item(component))
            else:
                older.refresh_component(component)
                children.append(older)

        self.children = children


class ModalStore:
    def __init__(self, state: ConnectionState) -> None:
        # (interaction_id, custom_id): Modal
        self._modals: Dict[Tuple[int, str], Modal] = {}
        self._state: ConnectionState = state

    def __verify_integrity(self) -> None:
        to_remove: List[Tuple[int, str]] = []
        for k, modal in self._modals.items():
            if modal.is_finished():
                to_remove.append(k)

        for k in to_remove:
            del self._modals[k]

    def add_modal(self, modal: Modal, user_id: int) -> None:
        self.__verify_integrity()

        modal._start_listening_from_store(self, user_id)
        self._modals[(user_id, modal.custom_id)] = modal  # type: ignore

    def remove_modal(self, modal: Modal, user_id: int) -> None:
        self._modals.pop((user_id, modal.custom_id))  # type: ignore

    def dispatch(self, custom_id: str, interaction: Interaction) -> None:
        self.__verify_integrity()
        key = (interaction.user.id, custom_id)  # type: ignore
        modal = self._modals.get(key)
        if modal is None:
            return

        data: ModalInteractionData = interaction.data  # type: ignore
        components = [component for row in data.get('components', []) for component in row['components']]
        modal.refresh([_component_factory(d) for d in components])

        asyncio.create_task(modal._scheduled_task(interaction), name=f'discord-ui-modal-dispatch-{modal.id}')
        self.remove_modal(modal, interaction.user.id)  # type: ignore
