
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
See class comment for details
"""
import json

from neuro_san import TOP_LEVEL_DIR
from neuro_san.internals.interfaces.dictionary_validator import DictionaryValidator
from neuro_san.service.mcp.validation.mcp_request_validator import McpRequestValidator
from neuro_san.service.mcp.session.mcp_session_manager import McpSessionManager

# MCP protocol version supported by this service
# Protocol specification is available at:
# https://modelcontextprotocol.io/specification/2025-06-18
MCP_VERSION: str = "2025-06-18"


class McpServerContext:
    """
    Class representing the server run-time context,
    necessary for handling MCP clients requests.
    """

    def __init__(self):
        self.protocol_schema_filepath = None
        self.protocol_schema = None
        self.session_manager = None
        self.request_validator = None
        self.enabled: bool = False

    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the MCP service.
        :param enabled: Flag indicating if the service should be enabled
        """
        if not self.enabled and enabled:
            print(">>>>>>>>>>>> Enabling MCP service...")
            # MCP service is being enabled, set it up:
            schema_name: str = f"service/mcp/validation/mcp-schema-{MCP_VERSION}.json"
            self.protocol_schema_filepath = TOP_LEVEL_DIR.get_file_in_basis(schema_name)
            try:
                with open(self.protocol_schema_filepath, "r", encoding="utf-8") as schema_file:
                    self.protocol_schema = json.load(schema_file)
                    self.request_validator = McpRequestValidator(self.protocol_schema)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                raise RuntimeError(f"Cannot load MCP protocol schema from "
                                   f"'{self.protocol_schema_filepath}': {str(exc)}") from exc
            # Create new session manager:
            self.session_manager = McpSessionManager()
        self.enabled = enabled

    def is_enabled(self) -> bool:
        """
        Check if the MCP service is enabled.
        :return: True if the service is enabled, False otherwise
        """
        return self.enabled

    def get_protocol_version(self) -> str:
        """
        Get the MCP protocol version supported by this service.
        :return: The MCP protocol version
        """
        return MCP_VERSION

    def get_request_validator(self) -> DictionaryValidator:
        """
        Get the request validator for this context.

        :return: The request validator
        """
        return self.request_validator

    def get_session_manager(self) -> McpSessionManager:
        """
        Get the MCP session manager for this context.
        :return: The session manager
        """
        return self.session_manager
