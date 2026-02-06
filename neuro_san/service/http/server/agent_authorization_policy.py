
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

from typing import Any
from typing import Dict

from os import environ

from neuro_san.service.authorization.factory.authorizer_factory import AuthorizerFactory
from neuro_san.service.authorization.interfaces.agent_authorizer import AgentAuthorizer
from neuro_san.service.authorization.interfaces.authorizer import Authorizer
from neuro_san.service.authorization.interfaces.permission import Permission
from neuro_san.service.generic.async_agent_service_provider import AsyncAgentServiceProvider


class AgentAuthorizationPolicy(AgentAuthorizer):
    """
    Abstract interface implementing some policy
    of allowing to route incoming requests to an agent.
    """

    def __init__(self, allowed_agents: Dict[str, AsyncAgentServiceProvider]):
        """
        Constructor

        :param allowed_agents: mapping from agent name to AsyncAgentServiceProvider
        """
        self.allowed_agents: Dict[str, AsyncAgentServiceProvider] = allowed_agents

        # Only need to get these once
        self.authorizer: Authorizer = AuthorizerFactory.create_authorizer()
        self.actor_key: str = environ.get("AGENT_AUTHORIZER_ACTOR_KEY", "User")
        self.actor_id_metadata_key: str = environ.get("AGENT_AUTHORIZER_ACTOR_ID_METADATA_KEY", "user_id")
        self.resource_key: str = environ.get("AGENT_AUTHORIZER_RESOURCE_KEY", "AgentNetwork")
        self.action: str = environ.get("AGENT_AUTHORIZER_ALLOW_ACTION", Permission.READ.value)

    async def allow(self, agent_name: str, metadata: Dict[str, Any]) -> AsyncAgentServiceProvider:
        """
        :param agent_name: name of an agent
        :return: instance of AsyncAgentService if routing requests is allowed for this agent;
                 None otherwise
        """
        # Prepare the input for the Authorizer
        actor_id: str = metadata.get(self.actor_id_metadata_key)
        actor: Dict[str, Any] = {
            "type": self.actor_key,
            "id": actor_id
        }

        resource: Dict[str, Any] = {
            "type": self.resource_key,
            "id": agent_name
        }

        # Consult the authorizer
        is_authorized: bool = self.authorizer.authorize(actor, self.action, resource)
        if not is_authorized:
            # Not authorized
            return None

        # The network still needs to exist.
        service_provider: AsyncAgentServiceProvider = self.allowed_agents.get(agent_name)
        return service_provider
