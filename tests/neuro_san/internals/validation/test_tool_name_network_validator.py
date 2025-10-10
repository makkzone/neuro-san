
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
from neuro_san.internals.validation.tool_name_network_validator import ToolNameNetworkValidator

from tests.neuro_san.internals.validation.abstract_network_validator_test import AbstractNetworkValidatorTest


class TestToolNameNetworkValidator(TestCase, AbstractNetworkValidatorTest):
    """
    Unit tests for ToolNameNetworkValidator class.
    """

    def create_validator(self) -> AgentNetworkValidator:
        """
        Creates an instance of the validator
        """
        return ToolNameNetworkValidator()

    def test_bad_name(self):
        """
        Tests a network where at least one of the nodes has a bad name
        """
        validator: AgentNetworkValidator = ToolNameNetworkValidator()

        # Open a known good network file
        config: Dict[str, Any] = self.restore("hello_world.hocon")

        # Invalidate per the test
        config["tools"][0]["name"] = "ann0un$er"

        errors: List[str] = validator.validate(config)
        self.assertEqual(1, len(errors))

    def test_deep_name(self):
        """
        Tests a network where at least one of the nodes has a reference to
        an exeternal network in a directory hierachy.
        """
        validator: AgentNetworkValidator = ToolNameNetworkValidator()

        # Open a known good network file
        config: Dict[str, Any] = self.restore("deep/math_guy_passthrough.hocon")

        errors: List[str] = validator.validate(config)
        self.assertEqual(0, len(errors))
