
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
from __future__ import annotations

from typing import Dict

from logging import getLogger
from logging import Logger
import os

from threading import get_ident
from threading import Lock  # DEF need async

from openfga_sdk.client.client import OpenFgaClient

from neuro_san.service.authorization.openfga.open_fga_init import OpenFgaInit


class OpenFgaClientCache:
    """
    Per the Open FGA docs here:
        https://github.com/openfga/python-sdk?tab=readme-ov-file#initializing-the-api-client

        "We strongly recommend you initialize the OpenFgaClient only once
         and then re-use it throughout your app..."

    Singleton factory for providing client access to OpenFGA server.
    Clients are preserved on a per-thread + per-store basis.

    In production code there will really only ever be a single fact data store
    (DEFAULT_STORE_NAME) for all the threads, but we will want all the threads
    to have their own client.

    In testing, however, we have the opposite: multiple stores for (likely)
    single threaded tests so that they specifically do not stomp on anything
    real code would use.
    """

    def __init__(self):
        """
        Constructor
        """

        # Note: Specifically using a synchronous lock here, as the idea is to
        #       manage a per-thread mapping of OpenFgaClient objects.
        self.lock: Lock = Lock()
        self.client_map: Dict[str, OpenFgaClient] = {}
        self.logger: Logger = getLogger(self.__class__.__name__)

    @classmethod
    def _get_instance(cls) -> OpenFgaClientCache:
        """
        :return: The singleton instance of this class
        """
        # pylint: disable=global-variable-not-assigned
        global INSTANCE     # noqa: F824
        return INSTANCE

    @classmethod
    await def get(cls, store_name: str = None) -> OpenFgaClient:
        """
        :return: The singleton instance of this class
        """
        if store_name is None:
            # This allows workaday code to not worry about store names,
            # including when it is called by unit tests.
            store_name = os.environ.get("AGENT_FGA_STORE_NAME", OpenFgaInit.DEFAULT_STORE_NAME)

        fga_client: OpenFgaClient = await cls._get_instance().get_client(store_name)
        return fga_client

    @staticmethod
    def get_map_key(store_name: str) -> str:
        """
        Generate a key into the client map for the given store name.

        OpenFGA recommends that we only initialize a single client for any app,
        but they do not talk about multithreaded apps at all. Looking in their
        client, it is not jumping out at me that it is thread-safe, so we allow
        one client per thread for the PMD Server via this key-generation method.

        :return: A client map key for the store name given the thread.
        """
        thread_id: int = get_ident()
        map_key: str = f"Thread-{thread_id}:{store_name}"
        return map_key

    async def get_client(self, store_name: str = None) -> OpenFgaClient:
        """
        :param store_name: The store name to use for fact storage.
                We expect workaday client code to not pass this in, but we allow
                a different store name as an arg so that test code can talk to an
                existing server without messing anything real up.
        :return: a connection to the OpenFGA authorization server for the given store name/
                thread id combination..
        """
        if store_name is None:
            # This allows workaday code to not worry about store names,
            # including when it is called by unit tests.
            store_name = os.environ.get("AGENT_FGA_STORE_NAME", OpenFgaInit.DEFAULT_STORE_NAME)

        # See if we have a client for the store name/thread id combo.
        map_key: str = self.get_map_key(store_name)
        with self.lock:

            fga_client: OpenFgaClient = self.client_map.get(map_key)
            if fga_client is None:

                self.logger.warning("No client for store_name %s", store_name)
                init = OpenFgaInit()
                fga_client = await init.initialize_client_for_store(store_name)

                self.client_map[map_key] = fga_client

        return fga_client

    def remove_for_testing(self, store_name: str, remove_from_map: bool = True):
        """
        Removes a store for testing purposes only.

        :param store_name: The store name to use for fact storage.
        :param remove_from_map: When True (the default) the entry will be
                removed from the store-name/thread map.
        """
        # See if we have a client for the store
        map_key: str = self.get_map_key(store_name)
        with self.lock:
            self._remove_key_for_testing(map_key, remove_from_map)

    def _remove_key_for_testing(self, map_key: str, remove_from_map: bool):
        """
        Removes a map key for testing purposes only.

        :param map_key: The store name to use for fact storage.
        :param remove_from_map: When True the entry will be
                removed from the store-name/thread map.
        """

        # Do not hold the lock as the caller will be holding for us.
        fga_client: OpenFgaClient = self.client_map.get(map_key)

        if fga_client is not None:

            # Do not actually remove the default store as that is what the app
            # will be using. Remove any other store for testing though.
            if OpenFgaInit.DEFAULT_STORE_NAME not in map_key:
                OpenFgaInit.remove_store_for_testing(fga_client)

            fga_client.close()
            if remove_from_map:
                del self.client_map[map_key]

    def reset_for_testing(self):
        """
        Reset the instance for testing purposes only.
        """
        with self.lock:

            if self.client_map is not None and len(self.client_map) > 0:

                # Close all the clients registered in the map
                # Need to add remove_from_map=False or else will get this error:
                #        "RuntimeError: dictionary changed size during iteration"
                for map_key in self.client_map:
                    self._remove_key_for_testing(map_key, remove_from_map=False)

                # Clear the map separately
                self.client_map = {}


# The global singleton instance
INSTANCE: OpenFgaClientCache = OpenFgaClientCache()
