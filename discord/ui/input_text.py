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

from typing import TYPE_CHECKING, TypeVar, Tuple, Optional, Type
import os

from .item import Item
from ..enums import ComponentType, InputTextStyle
from ..components import InputText as InputTextComponent

__all__ = (
    'InputText',
)

if TYPE_CHECKING:
    from .modal import Modal

    from ..types.components import (
        InputText as InputTextPayload,
    )

IT = TypeVar('IT', bound='InputText')
V = TypeVar('V', bound='None', covariant=True)

class InputText(Item):  # check if pyright is fine with this (no generic)
    """Represents a UI text input.

    .. note::

        :meth:`callback` will never be called.
        See :meth:`Modal.callback` for more information.

    .. versionadded:: 2.0

    Parameters
    ------------
    label: :class:`str`
        The label of the text input.
    style: :class:`discord.InputTextStyle`
        The style of the text input.
    custom_id: Optional[:class:`str`]
        The ID of the text input that gets received during an interaction.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is typed, if any.
    required: :class:`bool`
        Whether the text input is required. Defaults to ``True``.
    value: Optional[:class:`str`]
        The pre-filled text of the text input.
    min_length: Optional[:class:`int`]
        The minimum length of the text input.
    max_length: Optional[:class:`int`]
        The maximum length of the text input.
    row: Optional[:class:`int`]
        The relative row this text input belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    __item_repr_attributes__: Tuple[str, ...] = (
        'label',
        'style',
        'custom_id',
        'placeholder',
        'required',
        'value',
        'min_length',
        'max_length',
        'row',
    )

    def __init__(
        self,
        *,
        label: str,
        style: InputTextStyle,
        custom_id: Optional[str] = None,
        placeholder: Optional[str] = None,
        required: bool = True,
        value: Optional[str] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        row: Optional[int] = None,
    ):
        super().__init__()
        self._modal: Optional[Modal] = None
        self._received_value: Optional[str] = None
        self._provided_custom_id = custom_id is not None
        if custom_id is None:
            custom_id = os.urandom(16).hex()

        self._underlying = InputTextComponent._raw_construct(
            type=ComponentType.input_text,
            style=style,
            label=label,
            custom_id=custom_id,
            placeholder=placeholder,
            required=required,
            value=value,
            min_length=min_length,
            max_length=max_length,
        )
        self.row: Optional[int] = row

    @property
    def style(self) -> InputTextStyle:
        """:class:`discord.InputTextStyle`: The style of the text input."""
        return self._underlying.style

    @style.setter
    def style(self, value: InputTextStyle) -> None:
        if not isinstance(value, InputTextStyle):
            raise TypeError(f'style must be InputTextStyle not {value.__class__.__name__}')

        self._underlying.style = value

    @property
    def label(self) -> str:
        """:class:`str`: The label of the text input."""
        return self._underlying.label

    @label.setter
    def label(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError('label must be str')

        self._underlying.label = value

    @property
    def custom_id(self) -> str:
        return self._underlying.custom_id

    @custom_id.setter
    def custom_id(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError('custom_id must be str')

        self._underlying.custom_id = value

    @property
    def placeholder(self) -> Optional[str]:
        """Optional[:class:`str`]: The placeholder text that is shown if nothing is typed, if any."""
        return self._underlying.placeholder

    @placeholder.setter
    def placeholder(self, value: Optional[str]) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError('placeholder must be None or str')

        self._underlying.placeholder = value

    @property
    def min_length(self) -> Optional[int]:
        """Optional[:class:`int`]: The minimum length of the text input."""
        return self._underlying.min_length

    @min_length.setter
    def min_length(self, value: Optional[int]) -> None:
        if value is not None and not isinstance(value, int):
            raise TypeError('min_length must be None or int')

    @property
    def max_length(self) -> Optional[int]:
        """Optional[:class:`int`]: The maximum length of the text input."""
        return self._underlying.max_length

    @max_length.setter
    def max_length(self, value: Optional[int]) -> None:
        if value is not None and not isinstance(value, int):
            raise TypeError('max_length must be None or int')

    @property
    def required(self) -> bool:
        """:class:`bool`: Whether the text input is required."""
        return self._underlying.required

    @required.setter
    def required(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError('required must be bool')

        self._underlying.required = value

    @property
    def value(self) -> Optional[str]:
        """Optional[:class:`str`]: The received text from a user or the pre-filled text of the text input."""
        return self._received_value or self._underlying.value

    @value.setter
    def value(self, value: Optional[str]) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError('value must be None or str')

        self._underlying.value = value

    @classmethod
    def from_component(cls: Type[IT], component: InputTextComponent) -> IT:
        return cls(
            style=component.style,
            label=component.label,
            row=None,
        )

    @property
    def type(self) -> ComponentType:
        return self._underlying.type

    @property
    def width(self) -> int:
        return 5

    def to_component_dict(self) -> InputTextPayload:
        return self._underlying.to_dict()

    def refresh_component(self, component: InputTextComponent) -> None:
        self._underlying = component

    #         data: ModalInteractionData = interaction.data  # type: ignore
        # for component in data.get('components', []):
        #     if component['type'] == 1:
        #         for sub_component in component.get('components', []):
        #             if sub_component['type'] == 4:  # text input
        #                 # refactor this (style will be an unknown enum)
        #                 self._provided_values.append(sub_component)