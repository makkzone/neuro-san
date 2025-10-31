
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
"""
See class comment for details
"""
from typing import Any
from typing import Dict
from typing import List

from neuro_san.interfaces.concierge_session import ConciergeSession
from neuro_san.internals.network_providers.agent_network_storage import AgentNetworkStorage
from neuro_san.service.http.interfaces.agent_authorizer import AgentAuthorizer
from neuro_san.service.generic.async_agent_service import AsyncAgentService
from neuro_san.service.generic.async_agent_service_provider import AsyncAgentServiceProvider
from neuro_san.session.direct_concierge_session import DirectConciergeSession
from neuro_san.service.mcp.util.mcp_errors_util import McpErrorsUtil
from neuro_san.service.mcp.util.requests_util import RequestsUtil
from neuro_san.service.http.logging.http_logger import HttpLogger


class McpToolsProcessor:
    """
    Class implementing "tools"-related MCP requests.
    Overall MCP documentation can be found here:
    https://modelcontextprotocol.io/specification/2025-06-18/server/tools
    """

    def __init__(self,
                 logger: HttpLogger,
                 network_storage_dict: AgentNetworkStorage,
                 agent_policy: AgentAuthorizer):
        self.logger: HttpLogger = logger
        self.network_storage_dict: AgentNetworkStorage = network_storage_dict
        self.agent_policy: AgentAuthorizer = agent_policy

    async def list_tools(self, request_id, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        List available MCP tools.
        :param request_id: MCP request id;
        :param metadata: http-level request metadata;
        :return: json dictionary with tools list in MCP format
        """
        public_storage: AgentNetworkStorage = self.network_storage_dict.get("public")
        data: Dict[str, Any] = {}
        session: ConciergeSession = DirectConciergeSession(public_storage, metadata=metadata)
        result_dict: Dict[str, Any] = session.list(data)
        tools_description: List[Dict[str, Any]] = []
        for agent_dict in result_dict.get("agents", []):
            agent_name: str = agent_dict["agent_name"]
            tool_dict: Dict[str, Any] = await self._get_tool_description(agent_name, metadata)
            tools_description.append(tool_dict)
        return {
            "jsonrpc": "2.0",
            "id": RequestsUtil.safe_request_id(request_id),
            "result": {
                "tools": tools_description
            }
        }

    async def call_tool(self, request_id, metadata: Dict[str, Any], tool_name: str, prompt: str) -> Dict[str, Any]:
        """
        Call MCP tool, which executes neuro-san agent chat request.
        :param request_id: MCP request id;
        :param metadata: http-level request metadata;
        :param tool_name: tool name;
        :param prompt: input prompt as a string;
        :return: json dictionary with tool response in MCP format;
                 or json dictionary with error message in MCP format.
        """

        service_provider: AsyncAgentServiceProvider = self.agent_policy.allow(tool_name)
        if service_provider is None:
            # No such tool is found:
            return McpErrorsUtil.get_tool_error(request_id, f"Tool not found: {tool_name}")
        service: AsyncAgentService = service_provider.get_service()

        input_request: Dict[str, Any] = self._get_chat_input_request(prompt)
        response_text: str = ""
        try:
            result_generator = service.streaming_chat(input_request, metadata)
            async for result_dict in result_generator:
                partial_response: str = await self._extract_tool_response_part(result_dict)
                if partial_response is not None:
                    response_text = response_text + partial_response
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.logger.error(metadata, "Tool %s execution failed: %s", tool_name, str(exc))
            return McpErrorsUtil.get_tool_error(request_id, f"Failed to execute tool {tool_name}")

        # Return tool call result:
        return {
            "jsonrpc": "2.0",
            "id": RequestsUtil.safe_request_id(request_id),
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": RequestsUtil.safe_message(response_text)
                    }
                ],
                "isError": False
            }
        }

    async def _get_tool_description(self, agent_name: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        service_provider: AsyncAgentServiceProvider = self.agent_policy.allow(agent_name)
        if service_provider is None:
            return None
        service: AsyncAgentService = service_provider.get_service()
        function_dict: Dict[str, Any] = await service.function({}, metadata)
        tool_description: str = function_dict.get("function", {}).get("description", "")
        return {
            "name": agent_name,
            "description": tool_description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "text input for chat request"
                    }
                },
                "required": ["input"]
            }
        }

    async def _extract_tool_response_part(self, response_dict: Dict[str, Any]) -> str:
        response_part_dict: Dict[str, Any] = response_dict.get("response", {})
        response_type: str = response_part_dict.get("type", "")
        if response_type == "AGENT_FRAMEWORK":
            return response_part_dict.get("text", None)

    def _get_chat_input_request(self, input_text: str) -> Dict[str, Any]:
        """
        Construct Python dictionary expected by "streaming_chat" service API call.
        :param input_text: input user prompt;
        :return: "streaming_chat" service API input dictionary
        """
        return {
            "user_message": {
                "type": 2,
                "text": input_text
            },
            "chat_filter": {
                "chat_filter_type": "MAXIMAL"
            }
        }
