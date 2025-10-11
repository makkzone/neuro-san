
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

from neuro_san import REGISTRIES_DIR
from neuro_san.internals.graph.persistence.agent_network_restorer import AgentNetworkRestorer
from neuro_san.internals.graph.registry.agent_network import AgentNetwork
from neuro_san.internals.interfaces.dictionary_validator import DictionaryValidator
from neuro_san.test.interfaces.assert_forwarder import AssertForwarder


class AbstractNetworkValidatorTest(AssertForwarder):
    """
    Abstract base class for testing DictionaryValidators that process agent networks.

    We assume that subclasses will implement the create_validator method
    and also derive from unittest.TestCase.
    """

    def create_validator(self) -> DictionaryValidator:
        """
        Creates an instance of the validator
        """
        return NotImplementedError

    @staticmethod
    def restore(file_reference: str) -> Dict[str, Any]:
        # Open a known good network file
        restorer = AgentNetworkRestorer()
        hocon_file: str = REGISTRIES_DIR.get_file_in_basis(file_reference)
        agent_network: AgentNetwork = restorer.restore(file_reference=hocon_file)
        config: Dict[str, Any] = agent_network.get_config()
        return config

    def test_assumptions(self):
        """
        Can we construct?
        """
        validator: DictionaryValidator = self.create_validator()
        self.assertIsNotNone(validator)

    def test_empty(self):
        """
        Tests empty network
        """
        validator: DictionaryValidator = self.create_validator()

        errors: List[str] = validator.validate(None)
        self.assertEqual(1, len(errors))

        errors: List[str] = validator.validate({})
        self.assertEqual(1, len(errors))

    def test_valid(self, hocon_file: str = "hello_world.hocon"):
        """
        Tests a valid network
        """
        validator: DictionaryValidator = self.create_validator()

        # Open a known good network file
        config: Dict[str, Any] = self.restore(hocon_file)

        errors: List[str] = validator.validate(config)

        failure_message: str = None
        if len(errors) > 0:
            failure_message = errors[0]
        self.assertEqual(0, len(errors), failure_message)
