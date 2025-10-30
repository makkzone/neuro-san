
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
from typing import Any
from typing import Dict
from typing import Tuple

from neuro_san.service.http.logging.http_logger import HttpLogger
from neuro_san.service.utils.mcp_server_context import McpServerContext
from neuro_san.service.mcp.session.mcp_client_session import McpClientSession
from neuro_san.service.mcp.util.requests_util import RequestsUtil


class McpInitializeProcessor:
    """
    Class implementing client session initialization.
    """
    def __init__(self, mcp_context: McpServerContext, logger: HttpLogger):
        self.logger: HttpLogger = logger
        self.mcp_context: McpServerContext = mcp_context

    async def initialize_handshake(
            self,
            request_id,
            metadata: Dict[str, Any],
            params: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """
        Process initial protocol handshake.
        :param request_id: MCP request id;
        :param metadata: http-level request metadata;
        :param params: dictionary with handshake parameters;
        :return: json dictionary with handshake response
        """
        # Currently, we do not use any parameters from the client
        # for protocol version or capabilities negotiation.
        # We simply return the server capabilities.
        # Also: we don't look at possible session ID present in the incoming request.
        # Future versions may implement more complex negotiation logic.

        _ = params
        # Create new client session:
        session: McpClientSession = self.mcp_context.get_session_manager().create_session()
        session_id: str = session.get_id()
        self.logger.info(metadata, "Created new MCP client session with id: %s", session_id)

        response_dict: Dict[str, Any] =\
            {
                "jsonrpc": "2.0",
                "id": RequestsUtil.safe_request_id(request_id),
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {
                        "logging": {},
                        "prompts": {},
                        "resources": {},
                        "tools": {
                            "listChanged": False
                        }
                    },
                    "serverInfo": {
                        "name": "Neuro-san-MCPServer",
                        "title": "Neuro-san MCP Server",
                        "version": "1.0.0"
                    },
                    "instructions": ""
                }
            }
        return response_dict, session_id

    async def activate_session(
            self,
            session_id: str,
            metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Activate existing client session.
        :param session_id: session id to activate;
        :
        :param metadata: http-level request metadata;
        :return: True if successful;
                 False if session with given id does not exist
        """
        success: bool = self.mcp_context.get_session_manager().activate_session(session_id)
        if success:
            self.logger.info(metadata,
                             "Activated MCP client session with id: %s",
                             session_id)
        else:
            self.logger.info(metadata,
                             "Failed to activate MCP client session with id: %s - session not found",
                             session_id)
        return success
