
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

from unittest import TestCase

from neuro_san import REGISTRIES_DIR
from neuro_san.internals.chat.connectivity_reporter import ConnectivityReporter
from neuro_san.internals.graph.registry.agent_network import AgentNetwork
from neuro_san.internals.graph.persistence.agent_network_restorer import AgentNetworkRestorer


class TestConnectivityReporter(TestCase):
    """
    Unit tests for ConnectivityReporter class.
    """

    def test_assumptions(self):
        """
        Can we construct?
        """
        agent_network: AgentNetwork = None
        reporter = ConnectivityReporter(agent_network)
        self.assertIsNotNone(reporter)

    def get_sample_registry(self, hocon_file: str) -> AgentNetwork:
        """
        :param hocon_file: A hocon file reference within this repo
        """
        file_reference = REGISTRIES_DIR.get_file_in_basis(hocon_file)
        restorer = AgentNetworkRestorer()
        agent_network: AgentNetwork = restorer.restore(file_reference=file_reference)
        return agent_network

    def test_hello_world(self):
        """
        Tests the connectivity of the hello world hocon
        """
        agent_network: AgentNetwork = self.get_sample_registry("hello_world.hocon")
        reporter = ConnectivityReporter(agent_network)

        messages: List[Dict[str, Any]] = reporter.report_network_connectivity()
        self.assertEqual(len(messages), 2)

        # First guy is the front-man and he only has a single tool
        connectivity: Dict[str, Any] = messages[0]
        self.assertIsNotNone(connectivity)
        self.assertEqual(connectivity.get("display_as"), "llm_agent")

        tools: List[str] = connectivity.get("tools")
        self.assertIsNotNone(tools)
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0], "synonymizer")

        # Next guy is the synonymizer and has no tools
        connectivity: Dict[str, Any] = messages[1]
        self.assertIsNotNone(connectivity)
        self.assertEqual(connectivity.get("display_as"), "llm_agent")

        tools: List[str] = connectivity.get("tools")
        self.assertIsNotNone(tools)
        self.assertEqual(len(tools), 0)
