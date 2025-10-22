
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
from pathlib import Path, PurePosixPath

from neuro_san.internals.interfaces.agent_name_mapper import AgentNameMapper


class AgentFileTreeMapper(AgentNameMapper):
    """
    A simple policy implementation defining conversion
    between agent name as specified in a manifest file
    and a file path (relative to registry root directory) to this agent definition file.
    """
    def __init__(self, path_method=Path):
        """
        Constructor

        :param path_method: Optional Path method to use for path manipulations.
            Default is pathlib.Path, but can be overridden for testing purposes.
        """
        self.path_method = path_method

    def agent_name_to_filepath(self, agent_name: str) -> str:
        """
        Converts an agent name from registry manifest to file path to this agent definition file.
        """
        # agent_name from registry manifest uses '/' as separator,
        # we need to convert it to the local OS file path format.
        return str(self.path_method(PurePosixPath(agent_name)))

    def filepath_to_agent_network_name(self, filepath: str) -> str:
        """
        Converts a file path to agent definition file (relative to registry root directory)
        to agent network name identifying it to the service.
        """
        # Remove file name extension, convert it to "/" separator.
        # Specifically:
        # self.path_method(filepath).as_posix() - converts to Path format we use (default is OS native)
        #     and then to posix format (with '/' separator). This gets us a string.
        # PurePosixPath(...).with_suffix("") - converts string to a posix path (with "/")
        #     and removes the file extension.
        # str(...) - converts back to string.
        return str(PurePosixPath(self.path_method(filepath).as_posix()).with_suffix(""))
