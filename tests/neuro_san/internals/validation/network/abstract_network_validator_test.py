
# Copyright © 2023-2025 Cognizant Technology Solutions Corp, www.cognizant.com.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
