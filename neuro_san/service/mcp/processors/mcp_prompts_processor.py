
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
from neuro_san.service.mcp.util.requests_util import RequestsUtil


class McpPromptsProcessor:
    """
    Class implementing "prompts"-related MCP requests.
    https://modelcontextprotocol.io/specification/2025-06-18/server/prompts
    """

    def __init__(self, logger: HttpLogger):
        self.logger: HttpLogger = logger

    async def list_prompts(self, request_id, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        List available MCP promp templates.
        :param request_id: MCP request id;
        :param metadata: http-level request metadata;
        :return: json dictionary with prompts list in MCP format
        """
        _ = metadata
        return {
            "jsonrpc": "2.0",
            "id": RequestsUtil.safe_request_id(request_id),
            "result": {
                "prompts": []
            }
        }
