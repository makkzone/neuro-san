
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

from neuro_san.service.mcp.mcp_errors import McpError
from neuro_san.service.mcp.util.requests_util import RequestsUtil


class McpErrorsUtil:
    """
    Utility class for generating MCP protocol and tool error responses.
    """

    @classmethod
    def get_protocol_error(cls, request_id, error: McpError, extra_msg: str = None) -> Dict[str, Any]:
        """
        Generate a standard MCP protocol error response.
        :param request_id: MCP request id;
        :param error: MCPError enum value;
        :param extra_msg: Optional extra message to append to the standard error message;
        :return: json dictionary with error in MCP format suitable for sending to the client.
        """
        msg: str = error.str_label
        if extra_msg is not None:
            msg = f"{msg}: {extra_msg}"
        return {
            "jsonrpc": "2.0",
            # Appease code scanning tools by escaping the id field:
            "id": RequestsUtil.safe_request_id(request_id),
            "error": {
                "code": error.num_value,
                "message": RequestsUtil.safe_message(msg)
            }
        }

    @classmethod
    def get_tool_error(cls, request_id, error_msg: str) -> Dict[str, Any]:
        """
        Generate a standard MCP tool error response.
        :param request_id: MCP request id;
        :param error_msg: Error message to send to the client;
        :return: json dictionary with tool error in MCP format suitable for sending to the client.
        """
        return {
            "jsonrpc": "2.0",
            # Appease code scanning tools by escaping the id field:
            "id": RequestsUtil.safe_request_id(request_id),
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": RequestsUtil.safe_message(error_msg)
                    }
                ],
                "isError": True
            }
        }

    @classmethod
    def is_error(cls, response_dict: Dict[str, Any]) -> bool:
        """
        Check if the given MCP response dictionary represents an error.
        :param response_dict: MCP response dictionary;
        :return: True if the response is an error, False otherwise.
        """
        # Check for protocol error first:
        protocol_error = response_dict["error"]
        if protocol_error is not None and len(protocol_error) > 0:
            return True
        # Check for tool error:
        has_error: bool = response_dict.get("result", {}).get("isError", False)
        return has_error
