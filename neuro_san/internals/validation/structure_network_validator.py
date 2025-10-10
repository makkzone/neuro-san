
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
from typing import List

from neuro_san.internals.interfaces.agent_network_validator import AgentNetworkValidator
from neuro_san.internals.validation.composite_network_validator import CompositeNetworkValidator
from neuro_san.internals.validation.cycles_network_validator import CyclesNetworkValidator
from neuro_san.internals.validation.missing_nodes_network_validator import MissingNodesNetworkValidator
from neuro_san.internals.validation.unreachable_nodes_network_validator import UnreachableNodesNetworkValidator


class StructureNetworkValidator(CompositeNetworkValidator):
    """
    Implementation of CompositeNetworkValidator interface that uses multiple specific validators
    to do some standard validation for topological issues.
    This gets used by agent network designer.
    """

    def __init__(self):
        """
        Constructor
        """
        validators: List[AgentNetworkValidator] = [
            CyclesNetworkValidator(),
            MissingNodesNetworkValidator(),
            UnreachableNodesNetworkValidator(),
        ]
        super().__init__(validators)
