
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
