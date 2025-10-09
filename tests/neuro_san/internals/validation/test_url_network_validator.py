
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

from neuro_san import REGISTRIES_DIR
from neuro_san.internals.graph.persistence.agent_network_restorer import AgentNetworkRestorer
from neuro_san.internals.graph.registry.agent_network import AgentNetwork
from neuro_san.internals.validation.url_network_validator import UrlNetworkValidator


class TestUrlNetworkValidator(TestCase):
    """
    Unit tests for UrlNetworkValidator class.
    """

    def test_assumptions(self):
        """
        Can we construct?
        """
        validator = UrlNetworkValidator()
        self.assertIsNotNone(validator)

    def test_empty(self):
        """
        Tests empty network
        """
        validator = UrlNetworkValidator()

        errors: List[str] = validator.validate(None)
        self.assertEqual(1, len(errors))

        errors: List[str] = validator.validate({})
        self.assertEqual(1, len(errors))

    def test_valid(self):
        """
        Tests a valid network
        """
        validator = UrlNetworkValidator(subnetworks=["/math_guy"])

        # Open a known good network file
        restorer = AgentNetworkRestorer()
        hocon_file: str = REGISTRIES_DIR.get_file_in_basis("math_guy_passthrough.hocon")
        agent_network: AgentNetwork = restorer.restore(file_reference=hocon_file)
        config: Dict[str, Any] = agent_network.get_config()

        errors: List[str] = validator.validate(config)

        failure_message: str = None 
        if len(errors) > 0:
            failure_message = errors[0]
        self.assertEqual(0, len(errors), failure_message)

    def test_no_network(self):
        """
        Tests a network where at least one of the nodes does not have instructions
        """
        validator = UrlNetworkValidator(subnetworks=["/math_guy"])

        # Open a known good network file
        restorer = AgentNetworkRestorer()
        hocon_file: str = REGISTRIES_DIR.get_file_in_basis("math_guy_passthrough.hocon")
        agent_network: AgentNetwork = restorer.restore(file_reference=hocon_file)
        config: Dict[str, Any] = agent_network.get_config()

        # Invalidate per the test
        config["tools"][0]["tools"][0] = "/invalid_network"

        errors: List[str] = validator.validate(config)
        self.assertEqual(1, len(errors))
