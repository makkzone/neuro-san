
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
from typing import List

from logging import getLogger
from logging import Logger
import os

from openfga_sdk.client.models.check_request import ClientCheckRequest
from openfga_sdk.client.models.list_objects_request import ClientListObjectsRequest
from openfga_sdk.client.models.tuple import ClientTuple
from openfga_sdk.client.models.write_request import ClientWriteRequest
from openfga_sdk.models.check_response import CheckResponse
from openfga_sdk.models.list_objects_response import ListObjectsResponse
from openfga_sdk.models.read_request_tuple_key import ReadRequestTupleKey
from openfga_sdk.models.read_response import ReadResponse
from openfga_sdk.models.tuple_key import TupleKey
from openfga_sdk.sync import OpenFgaClient

from neuro_san.service.authorization.interfaces.authorizer import Authorizer


class OpenFgaAuthorizer(Authorizer):
    """
    Authorizer implementation for Open FGA ("Fine Grained Authorization").
    """

    def __init__(self, fga_client: OpenFgaClient = None):
        """
        Constructor

        :param fga_client: A pre-initialized OpenFgaClient
        """

        self.fga_client: OpenFgaClient = fga_client

        self.debug: bool = os.environ.get("DEBUG_AUTH") is not None
        self.fail_on_unauthorized: bool = os.environ.get("DEBUG_AUTH") == "hard"
        self.logger: Logger = getLogger(self.__class__.__name__)

    def authorize(self, actor: Dict[str, Any], action: str, resource: Dict[str, Any]) -> bool:
        """
        :param actor: The actor dictionary with the keys "type" and "id" identifying what
                      is seeking permission.  Most often this is of the form:
                        {
                            "type": "User",
                            "id": "<username>"
                        }
        :param action: The action for which the user is asking permission for.
                      Most often this is one of the strings "create", "read", "update" or "delete".
        :param resource: The resource dictionary with the keys "type" and "id" identifying
                      just what is to be authorized for use.  For instance:
                        {
                            "type": "AgentNetwork",
                            "id": "hello_world"
                        }
        :return: True if the actor is allowed to take the requested action on the resource.
                 False otherwise.
        """
        # Guilty until proven innocent
        authorized: bool = False

        # Create some local versions of args we might modify
        use_actor: Dict[str, Any] = actor
        use_action: str = action
        use_resource: Dict[str, Any] = resource

        # Fix case where values are Enum types.
        # OpenFGA needs everything to be JSON serializable, and the Enum types we have are not.
        if not isinstance(action, str):
            use_action = action.value
        if not isinstance(resource.get("type"), str):
            use_resource = {
                "type": resource.get("type").value,
                "id": resource.get("id")
            }

        # Useful in debugging
        if self.debug:
            self.logger.debug("authorize(%s, %s, %s:%s)", use_actor, use_action,
                              use_resource.get("type"), use_resource.get("id"))

        # Prepare a request to see if the server can tell us the answer.
        check_request = ClientCheckRequest(user=f"{use_actor.get('type')}:{use_actor.get('id')}",
                                           relation=use_action,
                                           object=f"{use_resource.get('type')}:{use_resource.get('id')}")

        check_response: CheckResponse = self.fga_client.check(check_request)
        authorized = check_response.allowed

        if not authorized:
            message: str = f"Actor: {actor}   action: {action}   resource: {resource}"
            if self.debug:
                self.logger.debug(message)
                self.logger.debug("authorized is %s", authorized)

            if self.fail_on_unauthorized:
                # Exception useful when trying to figure out where authorization
                # is being made in testing.
                raise ValueError(message)

        return authorized

    def list(self, actor: Dict[str, Any], relation: str, resource: Dict[str, Any]) -> List[str]:
        """
        Return a list of resource ids that the actor has the given relation to,
        as per the graph specified by the authorization model.

        :param actor: The actor dictionary with the keys "type" and "id" identifying what
                      entity's relation should be checked.  Most often this is of the form:
                        {
                            "type": "User",
                            "id": "<username>"
                        }
        :param relation: The relation for which the user's permissions will be checked.
                     Most often this is one of the strings from the Permission enum.

        :param resource: The resource dictionary with the keys "type" and "id" identifying
                      just what is to be authorized for use.  For instance:
                        {
                            "type": "AgentNetwork",
                            # Note: "id" is not specified. We want a list of these returned.
                        }
        :return: A list of resource ids that the actor has the given relation with.
                 An empty return list implies that the actor has access to no objects
                 of the given resource type.
        """
        # Initialize a return value
        ids: List[str] = []

        if resource.get("id") is not None:
            # We are looking for a specific id. Faster through authorize()
            if self.debug:
                self.logger.debug("using authorize() for list()")
            authorized: bool = self.authorize(actor, relation, resource)
            if authorized:
                ids.append(str(resource.get("id")))
            return ids

        # Formulate the user specification for the request
        actor_type: str = actor.get("type", "")
        actor_id: str = actor.get("id", "")
        request_user: str = None
        if len(actor_type) > 0 or len(actor_id) > 0:
            request_user = f"{actor_type}:{actor_id}"

        # Formulate the object/resource specification for the request
        resource_type: str = resource.get("type", "")

        if self.debug:
            self.logger.debug("list(%s, %s, %s:%s)", actor_id, relation, resource_type,  resource.get("id"))

        # Make the API call
        options: Dict[str, Any] = {}
        body = ClientListObjectsRequest(user=request_user,
                                        relation=relation,
                                        type=resource_type)
        response: ListObjectsResponse = self.fga_client.list_objects(body, options)

        for one_object in response.objects:
            # Results come in the format of a single string "<type>:<identifier>"
            one_id: str = one_object.split(":")[1]
            ids.append(one_id)

        return ids

    # pylint: disable=too-many-locals
    def query(self, actor: Dict[str, Any], relation: str, resource: Dict[str, Any]) -> List[str]:
        """
        Instead of a boolean answer from authorize() above, this method gives a list
        of resources of the given resource type (in the dict) that the actor has the
        *direct* given relation to.  This does not take authorization policy graphs
        into account.

        :param actor: The actor dictionary with the keys "type" and "id" identifying what
                      will be permitted.  Most often this is of the form:
                        {
                            "type": "User",
                            "id": "<username>"
                        }
        :param relation: The relation for which the user will be permitted.

        :param resource: The resource dictionary with the keys "type" and "id" identifying
                      just what is to be authorized for use.  For instance:
                        {
                            "type": "AgentNetwork",
                            "id": "hello_world"
                        }
        :return: A list of relations (which can be None or empty) that the actor
                has the given relation with.
        """

        # Formulate the user specification for the request
        actor_type: str = ""
        actor_id: str = ""
        if actor is not None:
            actor_type = actor.get("type", "")
            actor_id = actor.get("id", "")

        request_user: str = None
        if len(actor_type) > 0 or len(actor_id) > 0:
            request_user = f"{actor_type}:{actor_id}"

        # Formulate the object/resource specification for the request
        resource_type: str = resource.get("type", "")
        resource_id: str = resource.get("id", "")
        request_object: str = None
        if len(resource_type) > 0 or len(resource_id) > 0:
            request_object = f"{resource_type}:{resource_id}"

        # Make the API call
        options: Dict[str, Any] = {}
        body = ReadRequestTupleKey(user=request_user,
                                   relation=relation,
                                   object=request_object)
        response: ReadResponse = self.fga_client.read(body, options)

        # Process the response
        retval: List[str] = []
        for one_tuple in response.tuples:
            # one_tuple should be a openfga_sdk.models.tuple.Tuple
            key: TupleKey = one_tuple.key

            if request_user is None:
                # We were looking for a list of actors/users.
                user: str = key.user
                user = user.split(":")[1]
                retval.append(user)

            elif request_object is None:
                # We were looking for a list of resources.
                resource: str = key.object
                resource = resource.split(":")[1]
                retval.append(resource)

            elif relation is None:
                # We were looking for a list of relations.
                retval.append(key.relation)

        return retval

    def grant(self, actor: Dict[str, Any], relation: str, resource: Dict[str, Any]):
        """
        :param actor: The actor dictionary with the keys "type" and "id" identifying what
                      will be permitted.  Most often this is of the form:
                        {
                            "type": "User",
                            "id": "<username>"
                        }
        :param relation: The relation for which the user will be permitted.

        :param resource: The resource dictionary with the keys "type" and "id" identifying
                      just what is to be authorized for use.  For instance:
                        {
                            "type": "AgentNetwork",
                            "id": "hello_world"
                        }
        :return: Nothing
        """
        actor_type: str = actor.get("type", "")
        actor_id: str = actor.get("id", "")
        resource_type: str = resource.get("type", "")
        resource_id: str = resource.get("id", "")
        client_tuple = ClientTuple(user=f"{actor_type}:{actor_id}",
                                   relation=relation,
                                   object=f"{resource_type}:{resource_id}")

        if self.debug:
            self.logger.debug("Granting to %s:%s : %s on %s:%s", actor_type, actor_id,
                              relation, resource_type, resource_id)

        writes: List[ClientTuple] = []
        writes.append(client_tuple)

        # Previously some SpecialUser stuff used to go here.

        body = ClientWriteRequest(writes=writes, deletes=None)

        # Hard-won tip:
        # When this call fails with a ValidationError exception (an http 400 - Bad Request)
        # what is most likely happening is either:
        #   1)  something in the write() request given does not match what is
        #       allowed to be specified in the *.fga DSL file.
        #   2)  the auth policy you think is being uploaded to the auth server
        #       in open_fga_init() is not the one actually landing in the server.
        _ = self.fga_client.write(body)

    def revoke(self, actor: Dict[str, Any], relation: str, resource: Dict[str, Any]):
        """
        :param actor: The actor dictionary with the keys "type" and "id" identifying what
                      will no longer be permitted.  Most often this is of the form:
                        {
                            "type": "User",
                            "id": "<username>"
                        }
        :param relation: The relation for which the user will no longer be permitted.

        :param resource: The resource dictionary with the keys "type" and "id" identifying
                      just what is to be no longer authorized for use.  For instance:
                        {
                            "type": "AgentNetwork",
                            "id": "hello_world"
                        }
        :return: Nothing
        """
        actor_type: str = actor.get("type", "")
        actor_id: str = actor.get("id", "")
        resource_type: str = resource.get("type", "")
        resource_id: str = resource.get("id", "")
        client_tuple = ClientTuple(user=f"{actor_type}:{actor_id}",
                                   relation=relation,
                                   object=f"{resource_type}:{resource_id}")

        if self.debug:
            self.logger.debug("Revoking from %s:%s : %s on %s:%s", actor_type, actor_id,
                              relation, resource_type, resource_id)

        deletes: List[ClientTuple] = []
        deletes.append(client_tuple)
        body = ClientWriteRequest(writes=None, deletes=deletes)

        # Hard-won tip:
        # When this call fails with a ValidationError exception (an http 400 - Bad Request)
        # what is most likely happening is either:
        #   1)  something in the write() request given does not match what is
        #       allowed to be specified in the *.fga DSL file.
        #   2)  the auth policy you think is being uploaded to the auth server
        #       in open_fga_init() is not the one actually landing in the server.
        _ = self.fga_client.write(body)
