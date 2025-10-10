
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

import re

from neuro_san.internals.interfaces.agent_network_validator import AgentNetworkValidator


class ToolNameNetworkValidator(AgentNetworkValidator):
    """
    AgentNetworkValidator that looks for correct tool names in an agent network
    """

    # This comes from the langchain error message that happens when a tool name is not valid
    TOOL_NAME_PATTERN: str = r"^[a-zA-Z0-9_-]+$"

    def __init__(self):
        """
        Constructor
        """
        self.logger: Logger = getLogger(self.__class__.__name__)

    def validate(self, agent_network: Dict[str, Any]) -> List[str]:
        """
        Validate the agent network.

        :param agent_network: The agent network or name -> spec dictionary to validate
        :return: List of errors indicating agents and missing keywords
        """
        errors: List[str] = []

        self.logger.info("Validating agent network keywords...")

        if not agent_network:
            errors.append("Agent network is empty.")
            return errors

        # We can validate either from a top-level agent network,
        # or from the list of tools from the agent spec.
        name_to_spec: Dict[str, Any] = self.get_name_to_spec(agent_network)

        # Be sure all agent names are valid per the regex above.
        for agent_name, agent in name_to_spec.items():
            spec_name: str = agent.get("name")
            if not re.match(self.TOOL_NAME_PATTERN, agent_name) or \
                    not re.match(self.TOOL_NAME_PATTERN, spec_name):
                error_msg = f"{agent_name} must match the regex '{self.TOOL_NAME_PATTERN}'"
                errors.append(error_msg)

        # Only warn if there is a problem
        if len(errors) > 0:
            self.logger.warning(str(errors))

        return errors
