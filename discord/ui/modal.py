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

from typing import TYPE_CHECKING, Any, ClassVar, List, Optional, Dict
import os

from .item import ItemCallbackType
from .input_text import InputText
from .view import View, _ViewWeights
from ..utils import MISSING

if TYPE_CHECKING:
    from ..interactions import Interaction
    from ..types.interactions import ModalInteractionData

class Modal(View):
    """Represents a UI modal.

    This subclasses :class:`discord.ui.View` and implements similar functionality.
    One of the main differences between a :class:`discord.ui.Modal` and a :class:`discord.ui.View`
    is that it can have a maximum of 5 children instead of 25.

    .. note::

        :class:`discord.ui.InputText` objects are the only components currently supported in modals.
        This is a discord limitation.

    Parameters
    ----------
    timeout: Optional[:class:`float`]
        Timeout in seconds from last interaction with the UI before no longer accepting input.
        If ``None`` then there is no timeout.
    children: List[:class:`discord.ui.InputText`]
        The children of the modal.
        A modal can have a maximum of 5 children.
    title: Optional[:class:`str`]
        The title of the modal, if any.
    custom_id: :class:`str`
        The ID of the modal that gets received during an interaction.
        If not given then one is generated for you.
    """

    __discord_ui_modal__: ClassVar[bool] = True

    def __init_subclass__(cls) -> None:
        children: List[ItemCallbackType] = []
        for base in reversed(cls.__mro__):
            for member in base.__dict__.values():
                if hasattr(member, '__discord_ui_model_type__'):
                    children.append(member)

        if len(children) > 5:
            raise TypeError('View cannot have more than 5 children')

        cls.__view_children_items__ = children

    def __init__(
        self,
        *,
        title: str,
        timeout: Optional[float] = 180,
        custom_id: str = MISSING,
        children: List[InputText[Any]] = MISSING,
    ) -> None:
        super().__init__(timeout=timeout)
        self._provided_values: List[str] = []
        self._provided_custom_id: bool = custom_id is not MISSING
        self.title: str = title
        self.custom_id: str = os.urandom(16).hex() if custom_id is MISSING else custom_id

        if children is not MISSING:
            for item in children:
                self.add_item(item)

    def refresh_state(self, interaction: Interaction) -> None:
        data: ModalInteractionData = interaction.data  # type: ignore
        for component in data.get('components', []):
            if component['type'] == 3:  # select
                self._provided_values.extend(component.get('values', []))
            elif component['type'] == 4:  # text input
                self._provided_values.extend(component['value'])  # type: ignore

    async def callback(self, interaction: Interaction) -> None:
        """|coro|
        
        """
        pass

    @property
    def values(self) -> List[str]:
        """List[:class:`str]`: """
        return self._provided_values

    def to_callback_data(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'custom_id': self.custom_id,
            'components': self.to_components()
        }

    def is_persistent(self) -> bool:
        """:class:`bool`: Whether the modal is set up as persistent.

        A persistent modal has a set ``custom_id``, along with all of their components having
        a set ``custom_id`` as well. It also has a :attr:`timeout` set to ``None``.
        """
        return self.timeout is None and self._provided_custom_id and all(item.is_persistent() for item in self.children)

    def add_item(self, item: InputText[Any]) -> None:
        """Adds an item to the modal.

        Parameters
        -----------
        item: :class:`InputText`
            The item to add to the modal.

        Raises
        --------
        TypeError
            An :class:`InputText` was not passed.
        ValueError
            Maximum number of children has been exceeded (5)
            or the row the item is trying to be added to is full.
        """

        if len(self.children) > 5:
            raise ValueError('maximum number of children exceeded')

        if not isinstance(item, InputText):
            raise TypeError(f'expected Item not {item.__class__!r}')

        self.__weights.add_item(item)

        item._view = self
        self.children.append(item)
