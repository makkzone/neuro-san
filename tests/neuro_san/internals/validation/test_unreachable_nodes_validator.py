
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

from unittest import TestCase

from neuro_san.internals.interfaces.agent_network_validator import AgentNetworkValidator
from neuro_san.internals.validation.unreachable_nodes_network_validator import UnreachableNodesNetworkValidator

from tests.neuro_san.internals.validation.abstract_network_validator_test import AbstractNetworkValidatorTest


class TestUnreachableNodesNetworkValidator(TestCase, AbstractNetworkValidatorTest):
    """
    Unit tests for UnreachableNodesNetworkValidator class.
    """

    def create_validator(self) -> AgentNetworkValidator:
        """
        Creates an instance of the validator
        """
        return UnreachableNodesNetworkValidator()

    def test_multiple_front_men(self):
        """
        Tests a network where there is > 1 front man.
        """
        validator: AgentNetworkValidator = self.create_validator()

        # Open a known good network file
        config: Dict[str, Any] = self.restore("hello_world.hocon")

        # Invalidate per the test - remove the link between the announcer and synonymizer
        config["tools"][0]["tools"] = []

        errors: List[str] = validator.validate(config)
        self.assertEqual(1, len(errors))

    def test_unreachable(self):
        """
        Tests a network where there is an unreachable agent.
        """
        validator: AgentNetworkValidator = self.create_validator()

        # Open a known good network file
        config: Dict[str, Any] = self.restore("esp_decision_assistant.hocon")

        # Invalidate per the test - remove the link between the prescriptor and the predictor
        config["tools"][1]["tools"] = []

        errors: List[str] = validator.validate(config)

        self.assertEqual(1, len(errors), errors[-1])
