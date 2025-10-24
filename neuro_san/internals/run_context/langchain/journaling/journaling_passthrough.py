
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
from typing import Any
from typing import Dict
from typing import List

from copy import copy as shallow_copy

from pydantic import ConfigDict

from langchain_core.messages.ai import AIMessage
from langchain_core.messages.base import BaseMessage
from langchain_core.messages.tool import ToolMessage
from langchain_core.runnables.passthrough import RunnablePassthrough

from neuro_san.internals.journals.journal import Journal


class JournalingPassthrough(RunnablePassthrough, Journal):
    """
    RunnablePassthrough implementation that intercepts journal messages
    """

    # Declarations of member variables here satisfy Pydantic style,
    # which is a type validator that langchain is based on which
    # is able to use JSON schema definitions to validate fields.
    wrapped_journal: Journal

    origin: List[Dict[str, Any]]

    # This guy needs to be a pydantic class and in order to have
    # a non-pydantic Journal as a member, we need to do this.
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **kwargs: Any):
        """
        Constructor
        """
        # super().__init__(afunc=self.insert_framework_messages, **kwargs)
        super().__init__(afunc=self.identity, **kwargs)
        self._journaled: List[BaseMessage] = []

    async def write_message(self, message: BaseMessage, origin: List[Dict[str, Any]]):
        """
        Writes a BaseMessage entry into the journal
        :param message: The BaseMessage instance to write to the journal
        :param origin: A List of origin dictionaries indicating the origin of the run.
                The origin can be considered a path to the original call to the front-man.
                Origin dictionaries themselves each have the following keys:
                    "tool"                  The string name of the tool in the spec
                    "instantiation_index"   An integer indicating which incarnation
                                            of the tool is being dealt with.
        """
        # Forward on to the wrapped journal
        await self.wrapped_journal.write_message(message, origin)

        # Keep track of the messages coming through with the same origin
        if origin == self.origin:
            self._journaled.append(message)

    async def identity(self, inputs: Any) -> Any:
        """
        Do nothing to the input
        """
        return inputs

    async def insert_framework_messages(self, inputs: Any) -> Any:
        """
        Transform the input
        """
        if inputs is None:
            return None

        # See if there is anything journaled
        if not self._journaled:
            # Nothing to do
            return inputs

        if isinstance(inputs, AIMessage):
            return inputs

        # See if there are any input messages.
        input_messages: List[BaseMessage] = inputs.get("messages")
        if not input_messages:
            # Nothing to do
            return inputs

        outputs = shallow_copy(inputs)

        input_cursor: int = 0
        journal_cursor: int = 0
        output_messages: List[BaseMessage] = []
        while input_cursor < len(input_messages) and journal_cursor < len(self._journaled):

            journal_message: BaseMessage = self._journaled[journal_cursor]
            input_message: BaseMessage = input_messages[input_cursor]

            if journal_message.type == input_message.type and \
                    journal_message.content == input_message.content:
                # Append and advance both cursors
                output_messages.append(input_message)
                journal_cursor = min(journal_cursor + 1, len(self._journaled))
                input_cursor = min(input_cursor + 1, len(input_messages))
            elif isinstance(input_message, ToolMessage):
                # Append and advance only the input cursor
                output_messages.append(input_message)
                input_cursor = min(input_cursor + 1, len(input_messages))
            else:
                # Append and advance only the journal cursor
                output_messages.append(journal_message)
                journal_cursor = min(journal_cursor + 1, len(self._journaled))

        outputs["messages"] = output_messages

        return outputs
