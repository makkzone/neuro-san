
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

from neuro_san.internals.interfaces.dictionary_validator import DictionaryValidator
from neuro_san.internals.validation.network.missing_nodes_network_validator import MissingNodesNetworkValidator

from tests.neuro_san.internals.validation.network.abstract_network_validator_test import AbstractNetworkValidatorTest


class TestMissingNodesNetworkValidator(TestCase, AbstractNetworkValidatorTest):
    """
    Unit tests for MissingNodesNetworkValidator class.
    """

    def create_validator(self) -> DictionaryValidator:
        """
        Creates an instance of the validator
        """
        return MissingNodesNetworkValidator()

    def test_missing_nodes(self):
        """
        Tests a network where there is an unreachable agent.
        """
        validator: DictionaryValidator = self.create_validator()

        # Open a known good network file
        config: Dict[str, Any] = self.restore("esp_decision_assistant.hocon")

        # Invalidate per the test - add a node at the predictor
        config["tools"][2]["tools"] = ["missing_node"]

        errors: List[str] = validator.validate(config)

        self.assertEqual(1, len(errors), errors[-1])
