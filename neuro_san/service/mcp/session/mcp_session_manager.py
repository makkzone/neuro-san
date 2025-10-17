
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
import threading

from typing import Any
from typing import Dict
from typing import List

import uuid
import base64

from neuro_san.service.mcp.session.mcp_client_session import MCPClientSession

class MCPSessionManager:
    """
    Class creating and managing client sessions with the MCP service.
    """

    def __init__(self):
        # Lock to protect access to the sessions dictionary
        self.lock: threading.Lock = threading.Lock()
        self.sessions: Dict[str, MCPClientSession] = {}

    def create_session(self) -> MCPClientSession:
        """
        Create a new client session with the given client id.

        :return: The created MCPClientSession
        """
        with self.lock:
            if client_id in self.sessions:
                raise ValueError(f"Session with client id {client_id} already exists")
            session = MCPClientSession()
            self.sessions[client_id] = session
            return session

    def _generate_id(self) -> str:
        """
        Generate a new unique session id.
        :return: The generated session id
        """
        # Generate 128-bit random UUID (cryptographically secure)
        raw = uuid.uuid4().bytes
        # Encode to Base32 (A–Z, 2–7), remove '=' padding
        token = base64.b32encode(raw).decode('ascii').rstrip('=')
        # Take first 16 characters (still ~80 bits entropy — plenty for uniqueness)
        token = token[:16]
        # Format as 4x4 groups
        return '-'.join(token[i:i + 4] for i in range(0, 16, 4))