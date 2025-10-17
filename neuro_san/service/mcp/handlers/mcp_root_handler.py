
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
"""
See class comment for details
"""

import json
import os
from typing import Any
from typing import List
from typing import Dict

import jsonschema

from neuro_san.service.http.handlers.base_request_handler import BaseRequestHandler
from neuro_san.internals.network_providers.agent_network_storage import AgentNetworkStorage
from neuro_san.service.http.interfaces.agent_authorizer import AgentAuthorizer
from neuro_san.service.http.logging.http_logger import HttpLogger
from neuro_san.service.mcp.context.mcp_server_context import MCPServerContext
from neuro_san.service.mcp.util.mcp_errors_util import MCPErrorsUtil
from neuro_san.service.mcp.mcp_errors import MCPError
from neuro_san.service.mcp.processors.mcp_tools_processor import MCPToolsProcessor
from neuro_san.service.mcp.processors.mcp_resources_processor import MCPResourcesProcessor
from neuro_san.service.mcp.processors.mcp_prompts_processor import MCPPromptsProcessor
from neuro_san.service.mcp.processors.mcp_initialize_processor import MCPInitializeProcessor


class MCPRootHandler(BaseRequestHandler):
    # pylint: disable=attribute-defined-outside-init
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    def initialize(self,
                   agent_policy: AgentAuthorizer,
                   forwarded_request_metadata: List[str],
                   mcp_context: MCPServerContext,
                   network_storage_dict: Dict[str, AgentNetworkStorage]):
        """
        This method is called by Tornado framework to allow
        injecting service-specific data into local handler context.
        :param agent_policy: abstract policy for agent requests
        :param forwarded_request_metadata: request metadata to forward.
        :param mcp_context: MCP server context to use
        :param network_storage_dict: A dictionary of string (describing scope) to
                    AgentNetworkStorage instance which keeps all the AgentNetwork instances
                    of a particular grouping.
        """

        self.agent_policy = agent_policy
        self.forwarded_request_metadata: List[str] = forwarded_request_metadata
        self.mcp_context: MCPServerContext = mcp_context
        self.logger = HttpLogger(forwarded_request_metadata)
        self.network_storage_dict: Dict[str, AgentNetworkStorage] = network_storage_dict
        self.show_absent: bool = os.environ.get("SHOW_ABSENT_METADATA") is not None

        # Set default request_id for this request handler in case we will need it:
        BaseRequestHandler.request_id += 1

        if os.environ.get("AGENT_ALLOW_CORS_HEADERS") is not None:
            self.set_header("Access-Control-Allow-Origin", "*")
            self.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            headers: str = "Content-Type, Transfer-Encoding"
            metadata_headers: str = ", ".join(forwarded_request_metadata)
            if len(metadata_headers) > 0:
                headers += f", {metadata_headers}"
            # Set all allowed headers:
            self.set_header("Access-Control-Allow-Headers", headers)


    async def post(self):
        """
        Implementation of top-level POST request handler for MCP call.
        """

        metadata: Dict[str, Any] = self.get_metadata()
        request_id = "unknown"

        print(f"R>>> {self.request}")
        print(f"R>>> {self.request.body}")

        try:
            # Parse JSON body
            data = json.loads(self.request.body)

            request_id = data.get("id", "absent")

            # Validate incoming RPC structure against MCP schema:
            jsonschema.validate(instance=data, schema=self.mcp_protocol_schema)

            method: str = data.get("method")
            if method == "initialize":
                handshake_processor: MCPInitializeProcessor = MCPInitializeProcessor(self.logger)
                result_dict: Dict[str, Any] = await handshake_processor.initialize_handshake(request_id, metadata, data["params"])
                self.set_status(200)
                self.write(result_dict)
            elif method == "tools/list":
                tools_processor: MCPToolsProcessor = MCPToolsProcessor(self.logger, self.network_storage_dict, self.agent_policy)
                result_dict: Dict[str, Any] = await tools_processor.list_tools(request_id, metadata)
                self.set_status(200)
                self.write(result_dict)
            elif method == "tools/call":
                tools_processor: MCPToolsProcessor = MCPToolsProcessor(self.logger, self.network_storage_dict, self.agent_policy)
                call_params: Dict[str, Any] = data.get("params", {})
                tool_name: str = call_params.get("name")
                prompt: str = call_params.get("arguments", {}).get("input", "")
                result_dict: Dict[str, Any] = await tools_processor.call_tool(request_id, metadata, tool_name, prompt)
                self.set_status(200)
                self.write(result_dict)
            elif method == "resources/list":
                resources_processor: MCPResourcesProcessor = MCPResourcesProcessor(self.logger)
                result_dict: Dict[str, Any] = await resources_processor.list_resources(request_id, metadata)
                self.set_status(200)
                self.write(result_dict)
            elif method == "prompts/list":
                prompts_processor: MCPPromptsProcessor = MCPPromptsProcessor(self.logger)
                result_dict: Dict[str, Any] = await prompts_processor.list_resources(request_id, metadata)
                self.set_status(200)
                self.write(result_dict)
            elif method == "initialize":
                handshake_processor: MCPInitializeProcessor = MCPInitializeProcessor(self.logger)
                result_dict: Dict[str, Any] = await handshake_processor.initialize_handshake(request_id, metadata, data["params"])
                self.set_status(200)
                self.write(result_dict)
            elif method == "notifications/initialized":
                pass
            else:
                # Method is not found/not supported
                extra_error: str = f"method {method} not found"
                error_msg: Dict[str, Any] =\
                    MCPErrorsUtil.get_protocol_error(request_id, MCPError.NoMethod, extra_error)
                self.set_status(400)
                self.write(error_msg)
                self.logger.error(self.get_metadata(), f"error: Method {method} not found")
        except json.JSONDecodeError as exc:
            error_msg: Dict[str, Any] =\
                MCPErrorsUtil.get_protocol_error(request_id, MCPError.ParseError, str(exc))
            self.set_status(400)
            self.write(error_msg)
            self.logger.error(self.get_metadata(), "error: Invalid JSON format")
        except jsonschema.exceptions.ValidationError as exc:
            error_msg: Dict[str, Any] =\
                MCPErrorsUtil.get_protocol_error(request_id, MCPError.InvalidRequest, str(exc))
            self.set_status(400)
            self.write(error_msg)
            self.logger.error(self.get_metadata(), "error: Invalid JSON/RPC request")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            error_msg: Dict[str, Any] =\
                MCPErrorsUtil.get_protocol_error(request_id, MCPError.ServerError, str(exc))
            self.set_status(500)
            self.write(error_msg)
            self.logger.error(self.get_metadata(), "error: Server error")
        finally:
            # We are done with response stream:
            self.do_finish()


