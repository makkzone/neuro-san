
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
from typing import Tuple
from typing import Type
from typing import Union

import traceback

from logging import Logger
from logging import getLogger

from pydantic import ConfigDict

from langchain_classic.callbacks.tracers.logging import LoggingCallbackHandler
from langchain_core.agents import AgentFinish
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages.ai import AIMessage
from langchain_core.messages.base import BaseMessage
from langchain_core.runnables.base import Runnable
from langchain_core.runnables.config import RunnableConfig
from langchain_core.runnables.passthrough import RunnablePassthrough
from langchain_core.runnables.utils import Input
from langchain_core.runnables.utils import Output

from leaf_common.config.resolver_util import ResolverUtil

from neuro_san.internals.errors.error_detector import ErrorDetector
from neuro_san.internals.interfaces.invocation_context import InvocationContext
from neuro_san.internals.journals.intercepting_journal import InterceptingJournal
from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.messages.origination import Origination
from neuro_san.internals.run_context.interfaces.tool_caller import ToolCaller
from neuro_san.internals.run_context.langchain.journaling.journaling_callback_handler import JournalingCallbackHandler
from neuro_san.internals.run_context.langchain.token_counting.langchain_token_counter import LangChainTokenCounter
from neuro_san.internals.run_context.langchain.util.api_key_error_check import ApiKeyErrorCheck

MINUTES: float = 60.0

# Lazily import specific errors from llm providers
API_ERROR_TYPES: Tuple[Type[Any], ...] = ResolverUtil.create_type_tuple([
                                            "openai.APIError",
                                            "anthropic.APIError",
                                            "langchain_google_genai.chat_models.ChatGoogleGenerativeAIError",
                                         ])


class NeuroSanRunnable(RunnablePassthrough):
    """
    RunnablePassthrough implementation that intercepts journal messages
    """

    # Declarations of member variables here satisfy Pydantic style,
    # which is a type validator that langchain is based on which
    # is able to use JSON schema definitions to validate fields.
    agent_chain: Runnable

    primary_llm: BaseLanguageModel

    invocation_context: InvocationContext

    journal: Journal

    interceptor: InterceptingJournal

    origin: List[Dict[str, Any]]

    tool_caller: ToolCaller

    error_detector: ErrorDetector

    session_id: str

    # Default logger
    logger: Optional[Logger] = None

    # This guy needs to be a pydantic class and in order to have
    # a non-pydantic Journal as a member, we need to do this.
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Constructor
        """
        super().__init__(afunc=self.do_it, **kwargs)

    # pylint: disable=redefined-builtin
    async def do_it(self, inputs: Input) -> Output:
        """
        Transform a single input into an output.

        Args:
            inputs: The input to the `Runnable`.

        Returns:
            The output of the `Runnable`.
        """
        self.logger = getLogger(self.__class__.__name__)
        outputs: Dict[str, Any] = {}

        await self.main_invoke(inputs)

        return outputs

    async def main_invoke(self, inputs: Dict[str, Any]):
        """
        Workhorse

        :param inputs: Inputs to process
        """

        # Create an agent executor and invoke it with the most recent human message
        # as input.
        agent_spec: Dict[str, Any] = self.tool_caller.get_agent_tool_spec()

        verbose: Union[bool, str] = agent_spec.get("verbose", False)
        if isinstance(verbose, str):
            verbose = bool(verbose.lower() in ("true", "extra", "logging"))

        max_execution_seconds: float = agent_spec.get("max_execution_seconds", 2.0 * MINUTES)

        # Per advice from https://python.langchain.com/docs/how_to/migrate_agent/#max_iterations
        max_iterations: int = agent_spec.get("max_iterations", 20)
        recursion_limit: int = max_iterations * 2 + 1

        # Create the list of callbacks to pass when invoking
        parent_origin: List[Dict[str, Any]] = self.origin
        base_journal: Journal = self.invocation_context.get_journal()
        origination: Origination = self.invocation_context.get_origination()
        callbacks: List[BaseCallbackHandler] = [
            JournalingCallbackHandler(self.journal, base_journal, parent_origin, origination)
        ]

        # Consult the agent spec for level of verbosity as it pertains to callbacks.
        agent_spec: Dict[str, Any] = self.tool_caller.get_agent_tool_spec()
        verbose: Union[bool, str] = agent_spec.get("verbose", False)
        if isinstance(verbose, str) and verbose.lower() in ("extra", "logging"):
            # This particular class adds a *lot* of very detailed messages
            # to the logs.  Add this because some people are interested in it.
            callbacks.append(LoggingCallbackHandler(self.logger))

        runnable_config: Dict[str, Any] = self.prepare_runnable_config(self.session_id, callbacks, recursion_limit)

        # Chat history is updated in write_message
        recent_human_message: BaseMessage = inputs.get("input")
        await self.journal.write_message(recent_human_message)

        # Attempt to count tokens/costs while invoking the agent.
        token_counter = LangChainTokenCounter(self.primary_llm, self.invocation_context, self.journal, self.origin)
        await token_counter.count_tokens(self.invoke_agent_chain(inputs, runnable_config), max_execution_seconds)

    def prepare_runnable_config(self, session_id: str,
                                callbacks: List[BaseCallbackHandler] = None,
                                recursion_limit: int = None) -> Dict[str, Any]:
        """
        Prepare a RunnableConfig for a Runnable invocation.  See:
        https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.config.RunnableConfig.html

        :param session_id: An id for the run
        :param callbacks: A list of BaseCallbackHandlers to use for the run
        :param recursion_limit: Maximum number of times a call can recurse.
        :return: A dictionary to be used for a Runnable's invoke config.
        """

        # Set up a run name for tracing purposes
        request_metadata: Dict[str, Any] = self.invocation_context.get_metadata()
        request_id: str = request_metadata.get("request_id")
        request_prefix: str = ""
        if request_id is not None:
            request_prefix = f"{request_id}-"
        origin_name: str = Origination.get_full_name_from_origin(self.origin)
        run_name: str = f"{request_prefix}{origin_name}"

        # Add callbacks as an invoke config
        runnable_config: Dict[str, Any] = {
            "configurable": {
                "session_id": session_id
            },
            "run_name": run_name
        }

        # Add some optional stuff
        if callbacks:
            runnable_config["callbacks"] = callbacks

        if recursion_limit:
            runnable_config["recursion_limit"] = recursion_limit

        # Maybe add metadata to the config
        # DEF - get this from AGENT_USAGE_LOGGER_METADATA list. Plumbing likely required.
        runnable_keys: List[str] = ["request_id", "user_id"]
        runnable_metadata: Dict[str, Any] = {}
        for key in runnable_keys:
            value: Any = request_metadata.get(key)
            if value is not None:
                runnable_metadata[key] = value

        # Only add metadata if we have something
        if runnable_metadata:
            runnable_config["metadata"] = runnable_metadata

        return runnable_config

    async def invoke_agent_chain(self, inputs: Dict[str, Any], runnable_config: Dict[str, Any]):
        """
        Set the agent in motion

        :param inputs: The inputs to the agent_executor
        :param runnable_config: The runnable_config to send to the agent_executor
        """
        chain_result: Union[Dict[str, Any], AgentFinish, AIMessage] = None
        retries: int = 3
        exception: Exception = None
        backtrace: str = None
        while chain_result is None and retries > 0:
            try:
                chain_result: Dict[str, Any] = await self.agent_chain.ainvoke(input=inputs, config=runnable_config)
            except API_ERROR_TYPES as api_error:
                backtrace = traceback.format_exc()
                message: str = None
                if not ApiKeyErrorCheck.check_for_internal_error(backtrace):
                    # Does not look like internal LLM stack error:
                    message = ApiKeyErrorCheck.check_for_api_key_exception(api_error)
                if message is not None:
                    raise ValueError(message) from api_error
                # Continue with regular retry logic:
                self.logger.warning("retrying from %s", api_error.__class__.__name__)
                retries = retries - 1
                exception = api_error
            except KeyError as key_error:
                self.logger.warning("retrying from KeyError")
                retries = retries - 1
                exception = key_error
                backtrace = traceback.format_exc()
            except ValueError as value_error:
                response = str(value_error)
                find_string = "An output parsing error occurred. " + \
                              "In order to pass this error back to the agent and have it try again, " + \
                              "pass `handle_parsing_errors=True` to the AgentExecutor. " + \
                              "This is the error: Could not parse LLM output: `"
                if response.startswith(find_string):
                    # Agent is returning good stuff, but langchain is erroring out over it.
                    # From: https://github.com/langchain-ai/langchain/issues/1358#issuecomment-1486132587
                    # Per thread consensus, this is hacky and there are better ways to go,
                    # but removes immediate impediments.
                    chain_result = {
                        "output": response.removeprefix(find_string).removesuffix("`")
                    }
                else:
                    self.logger.warning("retrying from ValueError")
                    retries = retries - 1
                    exception = value_error
                    backtrace = traceback.format_exc()

        output: str = self.parse_chain_result(chain_result, exception, backtrace)
        return_message: BaseMessage = AIMessage(output)

        # Chat history is updated in write_message
        await self.journal.write_message(return_message)

    def parse_chain_result(self, chain_result: Union[Dict[str, Any], AgentFinish, AIMessage],
                           exception: Exception, backtrace: str) -> str:
        """
        Parse the result from the langchain chain.

        :param chain_result: The result from invoking the agent chain.
                        Can be:
                        * An AgentFinish instance whose return_values can be any one of the following
                        * A dictionary whose keys might be:
                            "output" - the actual output to use
                            "messages" - effectively a chat history
                        * An AIMessage whose content is the output to use
        :param exception: Any exception that happened along the way
        :param backtrace: Any backtrace to the exception that happened along the way
        :return: A string value to return as the result of the run.
        """

        # Initialize our output.
        # The value here might morph a bit between types, but when we return
        # something we expect it to be a string.
        output: Union[str, List[Dict[str, Any]]] = None

        if chain_result is None and exception is not None:
            # We got an exception instead of a proper result. Say so.
            output = f"Agent stopped due to exception {exception}"
        else:
            # Set some stuff up for later
            backtrace = None
            ai_message: AIMessage = None

            # Handle the AgentFinish case.
            # The return_values from there contain our output whether in string or dict form.
            # ??? From what path does this come?
            if isinstance(chain_result, AgentFinish):
                chain_result = chain_result.return_values

            if isinstance(chain_result, Dict):
                # Normal return value from a chain is a dict.
                # The dict in question usually has chat history in a messages field.
                # We want the last AIMessage from that chat history.
                messages: List[BaseMessage] = chain_result.get("messages", [])
                for message in reversed(messages):
                    if isinstance(message, AIMessage):
                        ai_message = message
                        break

                if ai_message is None:
                    # We didn't find an AIMessage, so look for straight-up output key
                    output = chain_result.get("output")

            elif isinstance(chain_result, AIMessage):
                # Sometimes we get an AIMessage from a tool call.
                ai_message = chain_result

            if ai_message is not None:
                # We generally want the content of any single AIMessage we found from above
                output = ai_message.content

        # In general, output is a string. but output from Anthropic can either be
        # a single string or a list of content blocks.
        # If it is a list, "text" is a key of a dictionary which is the first element of
        # the list. For more details: https://python.langchain.com/docs/integrations/chat/anthropic/#content-blocks
        if isinstance(output, list):
            output = output[0].get("text", "")

        # See if we had some kind of error and format accordingly, if asked for.
        output = self.error_detector.handle_error(output, backtrace)
        return output

    # pylint: disable=redefined-builtin
    def invoke(
        self,
        input: Input,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> Output:
        """
        Transform a single input into an output.
        """
        raise NotImplementedError
