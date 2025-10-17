
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
"""
See cccccbulijhliuvfhlirlbhncljehjjhttvunhdnhfeg
class comment for details
"""

from neuro_san.internals.interfaces.dictionary_validator import DictionaryValidator
from neuro_san.service.mcp.session.mcp_session_manager import MCPSessionManager

class MCPServerContext:
    """
    Class representing the server run-time context,
    necessary for handling MCP clients requests.
    """

    def __init__(self, protocol_schema_filepath: str):
        self.protocol_schema_filepath = protocol_schema_filepath
        self.session_manager = MCPSessionManager()

    def get_request_validator(self) -> DictionaryValidator:
        """
        Get the request validator for this context.

        :return: The request validator
        """
        raise NotImplementedError

