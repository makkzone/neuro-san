
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
import json

from neuro_san.internals.interfaces.dictionary_validator import DictionaryValidator
from neuro_san.service.mcp.validation.mcp_request_validator import MCPRequestValidator
from neuro_san.service.mcp.session.mcp_session_manager import MCPSessionManager

MCP_VERSION: str = "2025-06-18"

class MCPServerContext:
    """
    Class representing the server run-time context,
    necessary for handling MCP clients requests.
    """

    def __init__(self, protocol_schema_filepath: str):
        self.protocol_schema_filepath = protocol_schema_filepath
        self.session_manager = MCPSessionManager()
        self.request_validator = None
        try:
            with open(self.protocol_schema_filepath, "r", encoding="utf-8") as schema_file:
                self.protocol_schema = json.load(schema_file)
                self.request_validator = MCPRequestValidator(self.protocol_schema)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise RuntimeError(f"Cannot load MCP protocol schema from "
                               f"'{self.protocol_schema_filepath}': {str(exc)}") from exc

    def get_request_validator(self) -> DictionaryValidator:
        """
        Get the request validator for this context.

        :return: The request validator
        """
        return self.request_validator

    def get_session_manager(self) -> MCPSessionManager:
        """
        Get the MCP session manager for this context.
        :return: The session manager
        """
        return self.session_manager


