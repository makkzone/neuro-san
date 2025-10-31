
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
from typing import Optional

import os

from logging import Logger
from logging import getLogger

from pydantic import ConfigDict
from typing_extensions import override

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.messages.base import BaseMessage
from langchain_core.messages.base import messages_to_dict
from langchain_core.runnables.base import Other
from langchain_core.runnables.base import RunnableConfig
from langchain_core.runnables.passthrough import RunnablePassthrough
from langchain_core.runnables.utils import Input
from langchain_core.runnables.utils import Output

from neuro_san.internals.interfaces.invocation_context import InvocationContext
from neuro_san.internals.journals.intercepting_journal import InterceptingJournal
from neuro_san.internals.messages.origination import Origination


class NeuroSanRunnable(RunnablePassthrough):
    """
    RunnablePassthrough implementation that intercepts journal messages
    for a particular origin.
    """

    # Declarations of member variables here satisfy Pydantic style,
    # which is a type validator that langchain is based on which
    # is able to use JSON schema definitions to validate fields.
    invocation_context: InvocationContext

    interceptor: InterceptingJournal

    origin: List[Dict[str, Any]]

    session_id: str

    # Default logger
    logger: Optional[Logger] = None

    # This guy needs to be a pydantic class and in order to have
    # any non-pydantic non-serializable members, we need to do this.
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Constructor
        """
        super().__init__(afunc=self.run_it, **kwargs)
        self.logger: Logger = getLogger(self.__class__.__name__)

    # pylint: disable=redefined-builtin
    @override
    async def ainvoke(
        self,
        input: Other,
        config: RunnableConfig | None = None,
        **kwargs: Any | None,
    ) -> Other:

        _: Other = await super().ainvoke(input, config, **kwargs)
        outputs: Dict[str, Any] = self.get_intercepted_outputs()
        return outputs

    # pylint: disable=redefined-builtin
    async def run_it(self, inputs: Input) -> Output:
        """
        Transform a single input into an output.

        Args:
            inputs: The input to the `Runnable`.

        Returns:
            The output of the `Runnable`.
        """
        raise NotImplementedError

    def prepare_runnable_config(self, session_id: str = None,
                                callbacks: List[BaseCallbackHandler] = None,
                                recursion_limit: int = None,
                                use_run_name: bool = False) -> Dict[str, Any]:
        """
        Prepare a RunnableConfig for a Runnable invocation.  See:
        https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.config.RunnableConfig.html

        :param session_id: An id for the run
        :param callbacks: A list of BaseCallbackHandlers to use for the run
        :param recursion_limit: Maximum number of times a call can recurse.
        :return: A dictionary to be used for a Runnable's invoke config.
        """
        request_metadata: Dict[str, Any] = self.invocation_context.get_metadata()

        # Set up a run name for tracing purposes
        run_name: str = None
        if use_run_name:
            request_id: str = request_metadata.get("request_id")
            request_prefix: str = ""
            if request_id is not None:
                request_prefix = f"{request_id}-"
            origin_name: str = Origination.get_full_name_from_origin(self.origin)
            run_name: str = f"{request_prefix}{origin_name}"

        runnable_config: Dict[str, Any] = {}

        # Add some optional stuff
        if session_id:
            runnable_config["configurable"] = {
                "session_id": session_id
            }

        if run_name:
            runnable_config["run_name"] = run_name

        if callbacks:
            runnable_config["callbacks"] = callbacks

        if recursion_limit:
            runnable_config["recursion_limit"] = recursion_limit

        # Only add metadata if we have something
        runnable_metadata: Dict[str, Any] = self.prepare_tracing_metadata(request_metadata)
        if runnable_metadata:
            runnable_config["metadata"] = runnable_metadata

        return runnable_config

    def prepare_tracing_metadata(self, request_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare a dictionary of metadata for tracing purposes.

        :param request_metadata: The metadata to use for the run
        :return: A dictionary of metadata for run tracing
        """
        runnable_metadata: Dict[str, Any] = {}

        # Add values for listed env vars if they have values.
        # Defaults are standard env vars for kubernetes deployments
        env_vars_str: str = os.getenv("AGENT_TRACING_METADATA_ENV_VARS", "POD_NAME POD_NAMESPACE POD_IP NODE_NAME")
        if env_vars_str:
            env_vars: List[str] = env_vars_str.split(" ")
            for env_var in env_vars:
                value: str = os.getenv(env_var)
                if value:
                    runnable_metadata[env_var] = value

        request_keys: List[str] = ["request_id", "user_id"]
        for key in request_keys:
            value: Any = request_metadata.get(key)
            if value is not None:
                runnable_metadata[key] = value

        return runnable_metadata

    def get_intercepted_outputs(self) -> Dict[str, Any]:
        """
        :return: the intercepted outputs
        """
        intercepted_messages: List[BaseMessage] = self.interceptor.get_messages()

        messages: List[Dict[str, Any]] = messages_to_dict(intercepted_messages)
        outputs: Dict[str, Any] = {
            "messages": messages
        }
        return outputs
