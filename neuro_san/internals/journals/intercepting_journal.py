
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

from langchain_core.messages.base import BaseMessage

from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.messages.traced_message import TracedMessage


class InterceptingJournal(Journal):
    """
    A Journal implementation that intercepts messages for a specific origin en route
    to another wrapped Journal.
    """

    def __init__(self, wrapped_journal: Journal, origin: List[Dict[str, Any]]):
        """
        Constructor

        :param wrapped_journal: The journal to forward messages to
        :param origin: The origin dictionary to match for intercepts
        """
        self.wrapped_journal: Journal = wrapped_journal
        self.origin: List[Dict[str, Any]] = origin
        self.messages: List[BaseMessage] = []

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
        # Let the wrapped guy do what he's gunna do
        await self.wrapped_journal.write_message(message, origin)

        # Only consider messages that match the same origin as what we care about.
        if origin == self.origin:

            new_message: BaseMessage = message

            # When messages are TracedMessages, capture a version that
            # has all their fields translated to the additional_kwargs
            # for better display in tracing/observability applications like
            # LangSmith.
            if isinstance(message, TracedMessage):
                new_message = message.__class__(trace_source=message)

            self.messages.append(new_message)

    def get_messages(self) -> List[BaseMessage]:
        """
        :return: the intercepted messages
        """
        return self.messages
