
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

from os import environ

from leaf_common.config.resolver_util import ResolverUtil

from neuro_san.service.authorization.interfaces.authorizer import Authorizer
from neuro_san.service.authorization.null.null_authorizer import NullAuthorizer
from neuro_san.service.authorization.openfga.openfga_authorizer import OpenFgaAuthorizer


class AuthorizerFactory:
    """
    Factory class for getting the appropriate Authorizer instance
    """

    @staticmethod
    def create_authorizer(auth_type: str = None) -> Authorizer:
        """
        Factory method for creating the appropriate Authorizer instance
        :param auth_type: The type of authorization to use. If None (very common),
                        we default to the value in the environment variable AGENT_AUTHORIZER.
                        If that is not set, we default to NullAuthorizer.
        """
        authorizer: Authorizer = None

        if auth_type is None:

            auth_classname: str = environ.get("AGENT_AUTHORIZER")
            if auth_classname is not None and len(auth_classname) > 0:
                authorizer = ResolverUtil.create_instance(auth_classname,
                                                          "AGENT_AUTHORIZER env var",
                                                          Authorizer)
            else:
                authorizer = NullAuthorizer()
        elif auth_type == "openfga":
            authorizer = OpenFgaAuthorizer()
        else:
            authorizer = NullAuthorizer()

        return authorizer
