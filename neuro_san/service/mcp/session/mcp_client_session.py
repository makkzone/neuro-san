
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


class McpClientSession:
    """
    Class representing a client session with the MCP service.
    """

    def __init__(self, session_id: str):
        self.session_id: str = session_id

        # Flag indicating if the session is properly initialized
        # by handshake sequence and now active.
        self.session_is_active: bool = False

    def get_id(self) -> str:
        """
        Get the session id.
        """
        return self.session_id

    def is_active(self) -> bool:
        """
        Check if the session is active.
        """
        return self.session_is_active

    def set_active(self, is_active: bool) -> None:
        """
        Set the session active flag.
        """
        self.session_is_active = is_active
