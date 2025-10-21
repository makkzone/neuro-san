
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

from neuro_san.internals.interfaces.dictionary_validator import DictionaryValidator
from neuro_san.service.http.handlers.base_request_handler import BaseRequestHandler
from neuro_san.internals.network_providers.agent_network_storage import AgentNetworkStorage
from neuro_san.service.http.interfaces.agent_authorizer import AgentAuthorizer
from neuro_san.service.http.logging.http_logger import HttpLogger
from neuro_san.service.mcp.context.mcp_server_context import MCPServerContext
from neuro_san.service.mcp.session.mcp_session_manager import MCPSessionManager, MCP_SESSION_ID
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

        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
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

            # Validate incoming request content:
            request_validator: DictionaryValidator = self.mcp_context.get_request_validator()
            validation_errors = request_validator.validate(data)
            if validation_errors:
                extra_error: str = "; ".join(validation_errors)
                error_msg: Dict[str, Any] =\
                    MCPErrorsUtil.get_protocol_error(request_id, MCPError.InvalidRequest, extra_error)
                self.set_status(400)
                self.write(error_msg)
                self.logger.error(self.get_metadata(), f"Error: Invalid MCP request: {extra_error}")
                self.do_finish()
                return
        except json.JSONDecodeError as exc:
            error_msg: Dict[str, Any] = \
                MCPErrorsUtil.get_protocol_error(request_id, MCPError.ParseError, str(exc))
            self.set_status(400)
            self.write(error_msg)
            self.logger.error(self.get_metadata(), "error: Invalid JSON format")
            self.do_finish()
            return

        # We have valid MCP request:
        request_id = data.get("id", "absent")
        method: str = data.get("method")
        session_id: str = self.request.headers.get("Mcp-Session-Id", None)
        request_done: bool = False
        try:
            if method == "initialize":
                # Handle handshake/initialize session request
                handshake_processor: MCPInitializeProcessor = MCPInitializeProcessor(self.mcp_context, self.logger)
                result_dict, session_id = await handshake_processor.initialize_handshake(request_id, metadata, data["params"])
                self.set_header(MCP_SESSION_ID, session_id)
                self.set_status(200)
                self.write(result_dict)
                request_done = True
            elif method == "notifications/initialized":
                # Handle client acknowledgement of initialization response,
                # this activates the session on the server side for further operations.
                handshake_processor: MCPInitializeProcessor = MCPInitializeProcessor(self.mcp_context, self.logger)
                result: bool = await handshake_processor.activate_session(session_id, metadata)
                response_code: int = 202 if result else 404
                self.set_header(MCP_SESSION_ID, session_id)
                self.set_status(response_code)
                # We do not have any response body for this request
                request_done = True
        except Exception as exc:  # pylint: disable=broad-exception-caught
            error_msg: Dict[str, Any] = \
                MCPErrorsUtil.get_protocol_error(request_id, MCPError.ServerError, str(exc))
            self.set_status(500)
            self.write(error_msg)
            self.logger.error(self.get_metadata(), "error: Server error")
            request_done = True
        finally:
            # We are done with response stream:
            if request_done:
                self.do_finish()
                return

        # For all other methods, we need to have valid session:
        session_active: bool = False
        if session_id is not None:
            session_manager: MCPSessionManager = self.mcp_context.get_session_manager()
            session_active = session_manager.is_session_active(session_id)
        if not session_active:
            extra_error: str = "invalid or inactive session id"
            error_msg: Dict[str, Any] =\
                MCPErrorsUtil.get_protocol_error(request_id, MCPError.InvalidSession, extra_error)
            self.set_status(401)
            self.write(error_msg)
            self.logger.error(self.get_metadata(), f"error: {extra_error}")
            self.do_finish()
            return

        try:
            if method == "tools/list":
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
            else:
                # Method is not found/not supported
                extra_error: str = f"method {method} not found"
                error_msg: Dict[str, Any] =\
                    MCPErrorsUtil.get_protocol_error(request_id, MCPError.NoMethod, extra_error)
                self.set_status(400)
                self.write(error_msg)
                self.logger.error(self.get_metadata(), f"error: Method {method} not found")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            error_msg: Dict[str, Any] =\
                MCPErrorsUtil.get_protocol_error(request_id, MCPError.ServerError, str(exc))
            self.set_status(500)
            self.write(error_msg)
            self.logger.error(self.get_metadata(), "error: Server error")
        finally:
            # We are done with response stream:
            self.do_finish()

    async def delete(self):
        """
        Implementation of top-level DELETE request handler for MCP call.
        """

        metadata: Dict[str, Any] = self.get_metadata()
        request_id = "unknown"

        print(f"D>>> {self.request}")
        print(f"D>>> {self.request.body}")

        # We only expect MCP client session id taken from request headers:
        session_id: str = self.request.headers.get(MCP_SESSION_ID, None)
        if session_id is not None:
            print(f"D>>> session: {session_id}")

        request_status: int = 204
        if session_id is not None:
            session_manager: MCPSessionManager = self.mcp_context.get_session_manager()
            deleted: bool = session_manager.delete_session(session_id)
            if deleted:
                self.logger.info(metadata,f"Session %s deleted by client", session_id)
            else:
                extra_error: str = "Session id not found"
                error_msg: Dict[str, Any] =\
                    MCPErrorsUtil.get_protocol_error(request_id, MCPError.InvalidSession, extra_error)
                self.set_status(404)
                self.write(error_msg)
                self.logger.error(metadata, f"Error: {extra_error}")
        else:
            # No session id is provided in this request:
            # report bad request
            request_status = 401
        self.set_status(request_status)
        self.do_finish()

    async def get(self):
        # Consider GET request for MCP endpoint to be a service health check
        self.set_status(200)
        self.do_finish()


