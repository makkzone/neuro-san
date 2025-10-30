
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
from enum import Enum


class McpError(Enum):
    """
    Enum class for standard MCP error codes and brief messages.
    """
    # Standard and additional JSON-RPC 2.0 errors;
    # we keep naming consistent with JSON-RPC 2.0 spec.
    # pylint: disable=invalid-name
    ParseError = (-32700, "Parse error")
    InvalidRequest = (-32600, "Invalid Request")
    NoMethod = (-32601, "Method not found")
    InvalidParams = (-32602, "Invalid params")
    InternalError = (-32603, "Internal error")
    ServerError = (-32000, "Server error")
    InvalidSession = (-33000, "Invalid Session")
    InvalidProtocolVersion = (-33001, "Invalid Protocol Version")

    def __init__(self, num_value, str_label):
        self.num_value = num_value
        self.str_label = str_label
