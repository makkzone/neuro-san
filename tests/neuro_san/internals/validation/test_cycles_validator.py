
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
from neuro_san.internals.validation.cycles_network_validator import CyclesNetworkValidator

from tests.neuro_san.internals.validation.abstract_network_validator_test import AbstractNetworkValidatorTest


class TestCyclesNetworkValidator(TestCase, AbstractNetworkValidatorTest):
    """
    Unit tests for CyclesNetworkValidator class.
    """

    def create_validator(self) -> AgentNetworkValidator:
        """
        Creates an instance of the validator
        """
        return CyclesNetworkValidator()

    def test_cycles(self):
        """
        Tests a network where there is a cycle.
        These can actually be ok, but we want to test that we can detect them.
        """
        validator: AgentNetworkValidator = self.create_validator()

        # Open a known good network file
        config: Dict[str, Any] = self.restore("esp_decision_assistant.hocon")

        # Invalidate per the test - add a link from the predictor to the prescriptor
        config["tools"][2]["tools"] = ["prescriptor"]

        errors: List[str] = validator.validate(config)

        self.assertEqual(1, len(errors), errors[-1])
