
# Copyright © 2023-2026 Cognizant Technology Solutions Corp, www.cognizant.com.
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

"""
Command-line tool for validating HOCON agent network configuration files.

This script validates HOCON files against neuro-san's agent network validation rules,
checking for issues such as:
- Missing or unreachable agents
- Cyclical dependencies
- Invalid tool names
- Empty instructions
- Invalid URL references

Usage:
    python -m neuro_san.client.hocon_validator_cli path/to/agent.hocon
    python -m neuro_san.client.hocon_validator_cli path/to/agent.hocon --verbose
    python -m neuro_san.client.hocon_validator_cli path/to/agent.hocon --include-cycles
"""

from typing import Any
from typing import Dict
from typing import List

import argparse
import json
import sys

from pyparsing.exceptions import ParseException
from pyparsing.exceptions import ParseSyntaxException

from neuro_san.internals.interfaces.dictionary_validator import DictionaryValidator
from neuro_san.internals.graph.persistence.agent_network_restorer import AgentNetworkRestorer
from neuro_san.internals.validation.common.composite_dictionary_validator import (
    CompositeDictionaryValidator
)
from neuro_san.internals.validation.network.cycles_network_validator import CyclesNetworkValidator
from neuro_san.internals.validation.network.keyword_network_validator import KeywordNetworkValidator
from neuro_san.internals.validation.network.missing_nodes_network_validator import (
    MissingNodesNetworkValidator
)
from neuro_san.internals.validation.network.tool_name_network_validator import ToolNameNetworkValidator
from neuro_san.internals.validation.network.unreachable_nodes_network_validator import (
    UnreachableNodesNetworkValidator
)
from neuro_san.internals.validation.network.url_network_validator import UrlNetworkValidator


class HoconValidatorCli:
    """
    Command-line tool for validating HOCON agent network configuration files.
    """

    def __init__(self):
        """
        Constructor
        """
        self.args = None

    def main(self) -> int:
        """
        Main entry point for the HOCON validator CLI.

        :return: Exit code (0 for success, 1 for validation errors, 2 for other errors)
        """
        self.parse_args()

        try:
            config: Dict[str, Any] = self.load_hocon_file(self.args.hocon_file)
        except FileNotFoundError as exception:
            print(f"Error: File not found - {exception}", file=sys.stderr)
            return 2
        except (ParseException, ParseSyntaxException) as exception:
            print(f"Error: Failed to parse HOCON file - {exception}", file=sys.stderr)
            return 2
        except ValueError as exception:
            print(f"Error: {exception}", file=sys.stderr)
            return 2

        validator: DictionaryValidator = self.create_validator()
        errors: List[str] = validator.validate(config)

        if errors:
            print(f"Validation failed with {len(errors)} error(s):\n")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
            return 1

        print("Validation passed: No errors found.")
        if self.args.verbose:
            self.print_network_summary(config)
        return 0

    def parse_args(self):
        """
        Parse command line arguments.
        """
        arg_parser = argparse.ArgumentParser(
            description="Validate a HOCON agent network configuration file.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python -m neuro_san.client.hocon_validator_cli registries/hello_world.hocon
  python -m neuro_san.client.hocon_validator_cli my_agent.hocon --verbose
  python -m neuro_san.client.hocon_validator_cli my_agent.hocon --include-cycles
            """
        )

        arg_parser.add_argument(
            "hocon_file",
            type=str,
            help="Path to the HOCON file to validate"
        )

        arg_parser.add_argument(
            "--verbose",
            default=False,
            action="store_true",
            help="Print additional information about the agent network"
        )

        arg_parser.add_argument(
            "--include-cycles",
            default=False,
            action="store_true",
            dest="include_cycles",
            help="Include cycle detection in validation (cycles are allowed but flagged)"
        )

        arg_parser.add_argument(
            "--external-agents",
            type=str,
            default=None,
            dest="external_agents",
            help="Comma-separated list of valid external agent references (e.g., '/agent1,/agent2')"
        )

        arg_parser.add_argument(
            "--mcp-servers",
            type=str,
            default=None,
            dest="mcp_servers",
            help="Comma-separated list of valid MCP server URLs"
        )

        arg_parser.add_argument(
            "--json-output",
            default=False,
            action="store_true",
            dest="json_output",
            help="Output validation results as JSON"
        )

        self.args = arg_parser.parse_args()

    def load_hocon_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load and parse a HOCON file.

        :param file_path: Path to the HOCON file
        :return: Parsed configuration dictionary
        """
        restorer = AgentNetworkRestorer(registry_dir=None)
        agent_network = restorer.restore(file_reference=file_path)
        return agent_network.get_config()

    def create_validator(self) -> DictionaryValidator:
        """
        Create the composite validator based on command line arguments.

        :return: A DictionaryValidator instance
        """
        validators: List[DictionaryValidator] = [
            KeywordNetworkValidator(),
            MissingNodesNetworkValidator(),
            UnreachableNodesNetworkValidator(),
            ToolNameNetworkValidator(),
        ]

        if self.args.include_cycles:
            validators.append(CyclesNetworkValidator())

        external_agents: List[str] = None
        if self.args.external_agents:
            external_agents = [agent.strip() for agent in self.args.external_agents.split(",")]

        mcp_servers: List[str] = None
        if self.args.mcp_servers:
            mcp_servers = [server.strip() for server in self.args.mcp_servers.split(",")]

        validators.append(UrlNetworkValidator(external_agents, mcp_servers))

        return CompositeDictionaryValidator(validators)

    def print_network_summary(self, config: Dict[str, Any]):
        """
        Print a summary of the agent network.

        :param config: The agent network configuration
        """
        tools: List[Dict[str, Any]] = config.get("tools", [])

        print("\n--- Agent Network Summary ---")
        print(f"Total agents/tools defined: {len(tools)}")

        if tools:
            print("\nAgents:")
            for tool in tools:
                name: str = tool.get("name", "<unnamed>")
                has_instructions: bool = tool.get("instructions") is not None
                sub_tools: List[str] = tool.get("tools", [])
                tool_type: str = "LLM Agent" if has_instructions else "Coded Tool"
                print(f"  - {name} ({tool_type})")
                if sub_tools:
                    print(f"      Sub-tools: {', '.join(str(t) for t in sub_tools)}")

        metadata: Dict[str, Any] = config.get("metadata", {})
        if metadata:
            print(f"\nMetadata: {json.dumps(metadata, indent=2)}")


def main():
    """
    Entry point for the hocon_validator_cli module.
    """
    cli = HoconValidatorCli()
    exit_code: int = cli.main()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
