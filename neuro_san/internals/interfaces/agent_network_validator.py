
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


class AgentNetworkValidator:
    """
    An interface for validating agent network content.
    """

    def validate(self, agent_network: Dict[str, Any]) -> List[str]:
        """
        Validate the agent network

        :param agent_network: The agent network or name -> spec dictionary to validate
        :return: A list of error messages
        """
        raise NotImplementedError

    @staticmethod
    def get_name_to_spec(agent_network: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param agent_network: The top-level agent network or tools dictionary
        :return: The agent name -> single agent spec dictionary of the agent network
        """
        if agent_network is None:
            return None

        if "tools" not in agent_network:
            # Assume we already have the name -> spec dictionary
            return agent_network

        name_to_spec: Dict[str, Any] = {}
        agents: List[Dict[str, Any]] = agent_network.get("tools", [])
        for one_agent in agents:
            name_to_spec[one_agent.get("name")] = one_agent

        return name_to_spec

    @staticmethod
    def is_url_or_path(tool: str) -> bool:
        """
        Check if a tool string is a URL or file path (not an agent name).

        :param tool: The tool string to check
        :return: True if tool is a URL or path, False otherwise
        """
        return (tool.startswith("/") or
                tool.startswith("http://") or
                tool.startswith("https://"))

    @staticmethod
    def remove_dictionary_tools(down_chains: List[str]) -> List[str]:
        """
        Sometimes tool lists have dictionary entries to support servers-based tools
        that need more than just a string.  For instance MCP servers.
        :param  down_chains: List of tools
        :return: List of tools without dictionary entries
        """
        safe_list: List[str] = []
        for tool in down_chains:
            if isinstance(tool, str):
                safe_list.append(tool)
        return safe_list
