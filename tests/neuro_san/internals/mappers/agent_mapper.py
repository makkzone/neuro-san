
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

import unittest
from pathlib import PurePosixPath, PureWindowsPath

from neuro_san.internals.graph.persistence.agent_filetree_mapper import AgentFileTreeMapper
from neuro_san.internals.graph.persistence.agent_standalone_mapper import AgentStandaloneMapper


class TestMapper(unittest.TestCase):
    def test_posix_mapping(self):
        """
        Tests mapping on POSIX platforms
        """
        mapper = AgentFileTreeMapper(PurePosixPath)

        manifest_entry = "folder/subfolder/agent_definition.hocon"
        agent_filepath = mapper.agent_name_to_filepath(manifest_entry)
        self.assertEqual(agent_filepath, r"folder/subfolder/agent_definition.hocon")

        agent_network = mapper.filepath_to_agent_network_name(agent_filepath)
        self.assertEqual(agent_network, r"folder/subfolder/agent_definition")

    def test_windows_mapping(self):
        """
        Tests mapping on Windows platforms
        """
        mapper = AgentFileTreeMapper(PureWindowsPath)

        manifest_entry = "folder/subfolder/agent_definition.hocon"
        agent_filepath = mapper.agent_name_to_filepath(manifest_entry)
        self.assertEqual(agent_filepath, r"folder\subfolder\agent_definition.hocon")

        agent_network = mapper.filepath_to_agent_network_name(agent_filepath)
        self.assertEqual(agent_network, r"folder/subfolder/agent_definition")

    def test_standalone_posix_mapping(self):
        """
        Tests mapping on POSIX platforms
        """
        mapper = AgentStandaloneMapper(PurePosixPath)

        file_entry = r"/folder/subfolder/agent_definition.hocon"
        agent_filepath = mapper.agent_name_to_filepath(file_entry)
        self.assertEqual(agent_filepath, r"/folder/subfolder/agent_definition.hocon")

        agent_network = mapper.filepath_to_agent_network_name(agent_filepath)
        self.assertEqual(agent_network, r"agent_definition")

    def test_standalone_windows_mapping(self):
        """
        Tests mapping on Windows platforms
        """
        mapper = AgentStandaloneMapper(PureWindowsPath)

        file_entry = r"C:\folder\subfolder\agent_definition.hocon"
        agent_filepath = mapper.agent_name_to_filepath(file_entry)
        self.assertEqual(agent_filepath, r"C:\folder\subfolder\agent_definition.hocon")

        agent_network = mapper.filepath_to_agent_network_name(agent_filepath)
        self.assertEqual(agent_network, r"agent_definition")
