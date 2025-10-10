
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

from neuro_san.internals.interfaces.agent_network_validator import AgentNetworkValidator


class CompositeNetworkValidator(AgentNetworkValidator):
    """
    Implementation of the AgentNetworkValidator interface that uses multiple validators
    """

    def __init__(self, validators: List[AgentNetworkValidator]):
        """
        Constructor

        :param validators: A list of validators to use
        """
        self.validators = validators

    def validate(self, agent_network: Dict[str, Any]) -> List[str]:
        """
        Validate the agent network.

        :param agent_network: The agent network or name -> spec dictionary to validate
        :return: A list of error messages
        """
        errors: List[str] = []

        if not agent_network:
            errors.append("Agent network is empty.")
            return errors

        for validator in self.validators:
            errors.extend(validator.validate(agent_network))

        return errors
