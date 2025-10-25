
# Copyright (C) 2023-2025 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# neuro-san SDK Software in commercial settings.
#
# END COPYRIGHT
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Union

from langchain_core.messages.base import BaseMessage


class TracedMessage(BaseMessage):
    """
    Absstract BaseMessage implementation of a message that is to be sent over
    to be displayed in a LangSmith trace.

    LangSmith will only show content in its trace viewer when there are other
    fields filled in, even in additional kwargs. So this class makes all those fields
    visible by copying anything displayable into additional_kwargs.
    """

    def __init__(self, content: Union[str, List[Union[str, Dict]]] = "",
                 other: TracedMessage = None,
                 **kwargs: Any) -> None:
        """
        Pass in content as positional arg.

        Args:
            content: The string contents of the message.
            other: Another TracedMessage to copy additional_kwargs from.
            kwargs: Additional fields to pass to the
        """
        if other:
            # If the content is set to something other than None or an empty string,
            # that is all that LangSmith will ever show.  So put what we want to show
            # in the additional_kwargs with effectively null content.
            additional_kwargs: Dict[str, Any] = other.minimal_additional_kwargs()
            super().__init__(content="", additional_kwargs=additional_kwargs, **kwargs)
        else:
            super().__init__(content=content, **kwargs)

    @property
    def lc_serializable(self) -> bool:
        """
        Indicates if the object can be serialized by LangChain.
        """
        return True

    @property
    def lc_kwargs(self) -> Dict[str, Any]:
        """
        :return: the dictionary of keyword arguments for serialization.
        """
        raise NotImplementedError

    def minimal_additional_kwargs(self) -> Dict[str, Any]:
        """
        Creates a minimal additional_kwargs dictionary from the other
        :param other: The source to copy from
        :return: The minimal kwargs dictionary
        """

        additional_kwargs: Dict[str, Any] = {}

        for key, value in self.lc_kwargs.items():
            if self.is_displayable(key, value):
                additional_kwargs[key] = value

        return additional_kwargs

    def is_displayable(self, key: str, value: Any) -> bool:
        """
        :param key: The key to consider
        :param value: The value to consider
        :return: A boolean indicating whether the value for the key is displayable
                in the additional_kwargs
        """
        _ = key
        displayable: bool = value is not None and len(value) > 0
        return displayable
