
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

from langchain_core.messages.ai import AIMessage

from neuro_san.internals.messages.traced_message import TracedMessage


class AgentToolResultMessage(AIMessage, TracedMessage):
    """
    TracedMessage implementation of a message that came as a result from a tool.
    We use AIMessage class as a basis so that langchain can interpret the content
    correctly.  The extra field that we add here is an origin list to indicate
    where the the tool result came from.
    """

    tool_result_origin: Optional[List[Dict[str, Any]]] = None

    type: Literal["agent-tool-result"] = "agent-tool-result"

    def __init__(self, content: Union[str, List[Union[str, Dict]]] = "",
                 tool_result_origin: List[Dict[str, Any]] = None,
                 trace_source: AgentToolResultMessage = None,
                 **kwargs: Any) -> None:
        """
        Constructor

        :param content: The string contents of the message.
        :param tool_result_origin: A dictionary describing the origin of the tool result.
        :param trace_source: A message of the same type to prepare for tracing display
        :param kwargs: Additional fields to pass to initialize
        """
        super().__init__(content=content, trace_source=trace_source, **kwargs)
        self.tool_result_origin: List[Dict[str, Any]] = tool_result_origin

    @property
    def lc_kwargs(self) -> Dict[str, Any]:
        """
        :return: the keyword arguments for serialization.
        """
        return {
            "content": self.content,
            "tool_result_origin": self.tool_result_origin,
        }
