
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
from typing import Any
from typing import Dict

import asyncio
import contextlib
import json
import tornado

from neuro_san.service.generic.async_agent_service import AsyncAgentService
from neuro_san.service.http.handlers.base_request_handler import BaseRequestHandler


class StreamingChatHandler(BaseRequestHandler):
    """
    Handler class for neuro-san streaming chat API call.
    """

    async def post(self, agent_name: str):
        """
        Implementation of POST request handler for streaming chat API call.
        """

        metadata: Dict[str, Any] = self.get_metadata()
        service: AsyncAgentService = await self.get_service(agent_name, metadata)
        if service is None:
            return

        self.application.start_client_request(metadata, f"{agent_name}/streaming_chat")
        # Set up request timeout if it is specified:
        request_timeout: float = float(self.server_context.get_chat_request_timeout_seconds())
        if request_timeout <= 0.0:
            # For asyncio.timeout(), None means no timeout:
            request_timeout = None
        result_generator = None
        try:
            # Parse JSON body
            data = json.loads(self.request.body)

            # Set up headers for chunked response
            self.set_header("Content-Type", "application/json-lines")
            self.set_header("Transfer-Encoding", "chunked")
            # Flush headers immediately
            flush_ok: bool = await self.do_flush()
            if not flush_ok:
                # If we failed to flush our output,
                # most probably it's because connection is closed by a client.
                # Raise accordingly - we will handle this exception:
                raise tornado.iostream.StreamClosedError()

            async with asyncio.timeout(request_timeout):
                result_generator = service.streaming_chat(data, metadata)
                async for result_dict in result_generator:
                    result_str: str = json.dumps(result_dict) + "\n"
                    self.write(result_str)
                    flush_ok = await self.do_flush()
                    if not flush_ok:
                        # Raise exception to be handled as a general
                        # "stream abruptly closed" case:
                        raise tornado.iostream.StreamClosedError()

        except (asyncio.CancelledError, tornado.iostream.StreamClosedError):
            # ensure generator is closed promptly
            # and re-raise as recommended
            if result_generator is not None:
                # Suppress possible exceptions: they are of no interest here.
                with contextlib.suppress(Exception):
                    await result_generator.aclose()
                    result_generator = None
            self.logger.info(metadata, "Request handler cancelled/stream closed.")
            raise

        except asyncio.TimeoutError:
            # ensure generator is closed promptly
            if result_generator is not None:
                # Suppress possible exceptions: they are of no interest here.
                with contextlib.suppress(Exception):
                    await result_generator.aclose()
                    result_generator = None
            self.logger.info(metadata, "Chat request timeout for %s in %f seconds.", agent_name, request_timeout)
            # Recommended HTTP response code: Service Unavailable
            self.set_status(503)
            self.write({"error": "Request timeout"})

        except Exception as exc:  # pylint: disable=broad-exception-caught
            # Suppress possible exceptions: they are of no interest here.
            with contextlib.suppress(Exception):
                self.process_exception(exc)

        finally:
            # We are done with response stream:
            if result_generator is not None:
                with contextlib.suppress(Exception):
                    # It is possible we will call .aclose() twice
                    # on our result_generator - it is allowed and has no effect.
                    await result_generator.aclose()
            self.do_finish()
            self.application.finish_client_request(metadata, f"{agent_name}/streaming_chat", get_stats=True)
