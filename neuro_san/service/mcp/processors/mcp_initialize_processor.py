
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

from neuro_san.service.http.logging.http_logger import HttpLogger

class MCPInitializeProcessor:
    """
    Class implementing client session initialization.
    """
    def __init__(self, logger: HttpLogger):
        self.logger: HttpLogger = logger

    async def initialize_handshake(self, request_id, metadata: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process initial protocol handshake.
        :param request_id: MCP request id;
        :param metadata: http-level request metadata;
        :param params: dictionary with handshake parameters;
        :return: json dictionary with handshake response
        """

        _ = metadata
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
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
