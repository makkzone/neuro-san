
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
from typing import Set

from logging import getLogger
from logging import Logger

from neuro_san.internals.interfaces.agent_network_validator import AgentNetworkValidator


class StructureNetworkValidator(AgentNetworkValidator):
    """
    AgentNetworkValidator that looks for topological issues in an agent network.
    """

    # State tracking for graph visitation
    UNVISITED: int = 0
    CURRENTLY_BEING_PROCESSED: int = 1
    FULLY_PROCESSED: int = 2

    def __init__(self, cyclical_agents_ok: bool = False):
        """
        Constructor
        """
        self.logger: Logger = getLogger(self.__class__.__name__)
        self.cyclical_agents_ok: bool = cyclical_agents_ok

    def validate(self, agent_network: Dict[str, Any]) -> List[str]:
        """
        Comprehensive validation of the agent network structure.

        :param agent_network: The agent network or name -> spec dictionary to validate
        :return: List of any issues found.
        """
        errors: List[str] = []

        self.logger.info("Validating agent network structure...")

        if not agent_network:
            errors.append("Agent network is empty.")
            return errors

        # We can validate either from a top-level agent network,
        # or from the list of tools from the agent spec.
        name_to_spec: Dict[str, Any] = self.get_name_to_spec(agent_network)

        # Find top agents
        top_agents: Set[str] = self.find_all_top_agents(name_to_spec)

        if len(top_agents) == 0:
            errors.append("No top agent found in network")
        elif len(top_agents) > 1:
            errors.append(f"Multiple top agents found: {sorted(top_agents)}. Expected exactly one.")

        # Find cyclical agents
        cyclical_agents: Set[str] = self.find_cyclical_agents(name_to_spec)
        if cyclical_agents and not self.cyclical_agents_ok:
            errors.append(f"Cyclical dependencies found in agents: {sorted(cyclical_agents)}")

        # Find unreachable agents (only meaningful if we have exactly one top agent)
        unreachable_agents: Set[str] = set()
        if len(top_agents) == 1:
            top_agent: str = next(iter(top_agents))
            unreachable_agents = self.find_unreachable_agents(name_to_spec, top_agent)
            if unreachable_agents:
                errors.append(f"Unreachable agents found: {sorted(unreachable_agents)}")

        # Validate that agent tools have corresponding nodes
        missing_nodes: Dict[str, List[str]] = self.find_missing_agent_nodes(name_to_spec)
        if missing_nodes:
            for agent, missing_tools in missing_nodes.items():
                # Format the comma-separated list of missing tools
                tools_str: str = ", ".join(f"'{tool}'" for tool in missing_tools)
                errors.append(
                    f"Agent '{agent}' references non-existent agent(s) in tools: {tools_str}"
                )

        if len(errors) > 0:
            # Only warn if there is a problem
            self.logger.warning(str(errors))

        return errors

    def find_all_top_agents(self, name_to_spec: Dict[str, Any]) -> Set[str]:
        """
        Find all top agents - agents that have down-chains but are not down-chains of others.

        :param name_to_spec: The agent network to validate
        :return: Set of top agent names
        """
        all_down_chains: Set[str] = set()
        has_down_chains: Set[str] = set()

        for agent_name, agent_config in name_to_spec.items():
            down_chains: List[str] = agent_config.get("tools", [])
            if down_chains:

                has_down_chains.add(agent_name)

                safe_down_chains: List[str] = self.remove_dictionary_tools(down_chains)
                all_down_chains.update(safe_down_chains)

        # Potential top agents are agents that have down-chains but are not down-chains of others
        top_agents: Set[str] = has_down_chains - all_down_chains

        # Special case: If there's only one agent in the network, it's always a top agent
        if len(top_agents) == 0 and len(name_to_spec) == 1:
            # It's OK to have a single top agent with no down-chains
            one_top: str = list(name_to_spec.keys())[0]
            top_agents.add(one_top)

        return top_agents

    def find_cyclical_agents(self, name_to_spec: Dict[str, Any]) -> Set[str]:
        """
        Find agents that are part of cyclical dependencies using DFS.

        :param name_to_spec: The agent network to validate
        :return: Set of agent names that are part of cycles
        """
        # Step 1: Initialize state tracking for all agents
        state: Dict[str, int] = {}
        for agent in name_to_spec.keys():
            state[agent] = self.UNVISITED

        # Step 2: Set to collect all agents that are part of cycles
        cyclical_agents: Set[str] = set()

        # Step 3: Start DFS from each unvisited agent to ensure we check all components
        # (the network might have disconnected parts)
        for agent in name_to_spec.keys():
            if state[agent] == self.UNVISITED:  # Only start DFS from unvisited agents
                # Start DFS with empty path - this agent is the root of this search
                self.dfs_cycle_detection(name_to_spec, agent, [], state, cyclical_agents)

        # Step 4: Return all agents that were found to be part of cycles
        return cyclical_agents

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def dfs_cycle_detection(self, name_to_spec: Dict[str, Any], agent: str,
                            path: List[str], state: Dict[str, int], cyclical_agents: Set[str]):
        """
        Perform Depth-First Search (DFS) traversal to detect cycles starting from a specific agent.

        :param name_to_spec: The agent network to validate
        :param agent: Current agent being visited
        :param path: Current path from start to current agent (for cycle identification)
        :param state: Dictionary tracking visit state of all agents
        :param cyclical_agents: Set to collect all agents that are part of any cycle
        """
        # Step 1: Check if we've encountered an agent currently being processed (back edge = cycle)
        if state[agent] == self.CURRENTLY_BEING_PROCESSED:
            # Cycle detected! The agent is already in our current processing path
            cycle_start_idx: int = path.index(agent)  # Find where the cycle starts in our path
            cycle_agents: Set[str] = set(path[cycle_start_idx:] + [agent])  # Extract all agents in the cycle
            cyclical_agents.update(cycle_agents)  # Add them to our result set
            return

        # Step 2: Skip if this agent was already fully processed in a previous DFS
        if state[agent] == self.FULLY_PROCESSED:
            return  # Already completed, no need to process again

        # Step 3: Mark agent as currently being processed (prevents infinite recursion)
        state[agent] = self.CURRENTLY_BEING_PROCESSED

        # Step 4: Add current agent to the path (to track the route we took to get here)
        path.append(agent)

        # Step 5: Get all child agents (down_chains) of current agent
        agent_spec: Dict[str, Any] = name_to_spec.get(agent, {})
        down_chains: List[str] = agent_spec.get("tools", [])
        safe_down_chains: List[str] = self.remove_dictionary_tools(down_chains)

        # Step 6: Recursively visit each child agent
        for child_agent in safe_down_chains:
            # Only visit child if it exists in our network (safety check)
            if child_agent in name_to_spec:
                self.dfs_cycle_detection(name_to_spec, child_agent, path, state, cyclical_agents)

        # Step 7: Backtrack - remove current agent from path as we're done processing it
        path.pop()

        # Step 8: Mark agent as fully processed (all its descendants have been explored)
        state[agent] = self.FULLY_PROCESSED

    def find_unreachable_agents(self, name_to_spec: Dict[str, Any], top_agent: str) -> Set[str]:
        """
        Find agents that are unreachable from the top agent using Depth-First Search (DFS) traversal.

        :param name_to_spec: The agent network to validate
        :param top_agent: The single top agent to start from
        :return: Set of unreachable agent names
        """
        # Step 1: Initialize set to track all agents we can reach from top agent
        reachable_agents: Set[str] = set()

        # Step 2: Initialize visited set to track DFS traversal (prevents infinite loops in cycles)
        visited: Set[str] = set()

        # Step 3: Start DFS traversal from the top agent to find all reachable agents
        self.dfs_reachability_traversal(name_to_spec, top_agent, visited, reachable_agents)

        # Step 4: Get complete set of all agents in the network
        all_agents: Set[str] = set(name_to_spec.keys())

        # Step 5: Calculate unreachable agents by subtracting reachable from all agents
        unreachable_agents: Set[str] = all_agents - reachable_agents

        # Step 6: Return the set of agents that cannot be reached from top agent
        return unreachable_agents

    def dfs_reachability_traversal(self, name_to_spec: Dict[str, Any], agent: str,
                                   visited: Set[str], reachable_agents: Set[str]):
        """
        Perform DFS traversal to find all agents reachable from a specific starting agent.

        :param name_to_spec: The agent network to validate
        :param agent: Current agent being visited
        :param visited: Set of agents already visited in this traversal (prevents infinite loops)
        :param reachable_agents: Set to collect all agents that can be reached
        """
        # Step 1: Check if we've already visited this agent or if it doesn't exist in network
        if agent in visited or agent not in name_to_spec:
            return  # Skip already visited agents or non-existent agents

        # Step 2: Mark current agent as visited to prevent revisiting
        visited.add(agent)

        # Step 3: Add current agent to our reachable set
        reachable_agents.add(agent)

        # Step 4: Get all child agents (down_chains) of current agent
        down_chains: List[str] = name_to_spec.get(agent, {}).get("tools", [])
        safe_down_chains: List[str] = self.remove_dictionary_tools(down_chains)

        # Step 5: Recursively visit each child agent to continue the traversal
        for child_agent in safe_down_chains:
            # Skip URL/path tools - they're not agents
            if not self.is_url_or_path(child_agent):
                # Visit each child - the recursion will handle visited check and network existence
                self.dfs_reachability_traversal(name_to_spec, child_agent, visited, reachable_agents)

    def find_missing_agent_nodes(self, name_to_spec: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Find agents referenced in "tools" lists that don't have corresponding nodes in the network.

        :param name_to_spec: The agent network to validate
        :return: Dictionary mapping agent names to list of tools that reference non-existent agents
                Format: {agent_name: [missing_tool1, missing_tool2, ...]}
        """
        missing_nodes: Dict[str, List[str]] = {}

        # Iterate through all agents in the network
        for agent_name, agent_data in name_to_spec.items():

            tools: List[str] = agent_data.get("tools", [])
            safe_tools: List[str] = self.remove_dictionary_tools(tools)

            # Check each tool in the agent's tools list
            for tool in safe_tools:
                # Skip URL/path tools - they're not agents and don't need nodes
                if self.is_url_or_path(tool):
                    continue

                # If tool is an agent reference but has no node in network, it's invalid
                if tool not in name_to_spec:
                    if agent_name not in missing_nodes:
                        missing_nodes[agent_name] = []
                    missing_nodes[agent_name].append(tool)

        return missing_nodes

    def get_top_agent(self, name_to_spec: Dict[str, Any]) -> str:
        """
        Get the single top agent from a valid network.

        :param name_to_spec: The agent network to validate
        :return: Name of the top agent
        :raises ValueError: If network doesn't have exactly one top agent
        """
        top_agents: Set[str] = self.find_all_top_agents(name_to_spec)

        if len(top_agents) == 0:
            raise ValueError("No top agent found in network")

        if len(top_agents) > 1:
            raise ValueError(f"Multiple top agents found: {sorted(top_agents)}. Expected exactly one.")

        top_agent: str = next(iter(top_agents))
        return top_agent
