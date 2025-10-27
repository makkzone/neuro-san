
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
from typing import Literal
from typing import Optional
from typing import Union

from neuro_san.internals.messages.traced_message import TracedMessage


class AgentMessage(TracedMessage):
    """
    TracedMessage implementation of a message from an agent
    """

    structure: Optional[Dict[str, Any]] = None

    type: Literal["agent"] = "agent"

    def __init__(self, content: Union[str, List[Union[str, Dict]]] = "",
                 structure: Dict[str, Any] = None,
                 trace_source: AgentMessage = None,
                 **kwargs: Any) -> None:
        """
        Constructor

        :param content: The string contents of the message.
        :param structure: A dictionary to pack into the message
        :param trace_source: A message of the same type to prepare for tracing display
        :param kwargs: Additional fields to pass to initialize
        """
        super().__init__(content=content, trace_source=trace_source, **kwargs)
        self.structure: Dict[str, Any] = structure

    @property
    def lc_kwargs(self) -> Dict[str, Any]:
        """
        :return: the keyword arguments for serialization.
        """
        return {
            "content": self.content,
            "structure": self.structure,
        }
