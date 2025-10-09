
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

from typing import Any
from typing import Dict
from typing import List

from logging import getLogger
from logging import Logger

from neuro_san.internals.interfaces.agent_network_validator import AgentNetworkValidator


class UrlNetworkValidator(AgentNetworkValidator):
    """
    AgentNetworkValidator that looks for correct URLs in an agent network
    """

    def __init__(self, subnetworks: List[str] = None, mcp_servers: List[str] = None):
        """
        Constructor

        :param subnetworks: A list of subnetworks
        :param mcp_servers: A list of MCP servers, as read in from a mcp_info.hocon file
        """
        self.logger: Logger = getLogger(self.__class__.__name__)
        self.subnetworks: List[str] = subnetworks
        self.mcp_servers: List[str] = mcp_servers

    def validate(self, agent_network: Dict[str, Any]) -> List[str]:
        """
        Check if URL of MCP servers and subnetworks are valid.

        :param agent_network: The agent network or name -> spec dictionary to validate
        :return: List of errors indicating invalid URL
        """
        errors: List[str] = []

        if not agent_network:
            errors.append("Agent network is empty.")
            return errors

        # We can validate either from a top-level agent network,
        # or from the list of tools from the agent spec.
        name_to_spec: Dict[str, Any] = self.get_name_to_spec(agent_network)

        # Compile list of urls to check
        urls: List[str] = []
        if self.subnetworks:
            urls.extend(self.subnetworks)
        if self.mcp_servers:
            urls.extend(self.mcp_servers)

        self.logger.info("Validating URLs for MCP tools and subnetwork...")

        for agent_name, agent in name_to_spec.items():
            if agent.get("tools"):
                tools: List[str] = agent.get("tools")
                if tools:
                    for tool in tools:
                        if self.is_url_or_path(tool) and tool not in urls:
                            error_msg = f"Agent '{agent_name}' has invalid URL or path in tools: '{tool}' urls: {urls}"
                            errors.append(error_msg)

        return errors

    def is_url_or_path(self, tool: str) -> bool:
        """
        Check if a tool string is a URL or file path (not an agent name).

        :param tool: The tool string to check
        :return: True if tool is a URL or path, False otherwise
        """
        return (tool.startswith("/") or
                tool.startswith("http://") or
                tool.startswith("https://"))
