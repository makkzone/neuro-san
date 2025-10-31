
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
from typing import Any
from typing import List

from asyncio import run

from neuro_san.internals.run_context.openai.openai_client import OpenAIClient


class ResourcesCli:
    """
    Command line app to list/clean up OpenAI Resources
    that had not been cleaned up before.
    """

    def __init__(self):
        """
        Constructor
        """
        self.client = OpenAIClient()

    async def get_assistant_ids(self) -> List[Any]:
        """
        :return: The list of assistant ids associated with the client
        """
        assistants_list = await self.client.list_assistants()
        assistant_ids = []
        for assistant in assistants_list:
            assistant_ids.append(assistant.id)
        return assistant_ids

    async def main_loop(self):
        """
        Do the work of cleaning up all outstanding assistants.
        """
        assistant_ids = await self.get_assistant_ids()
        while len(assistant_ids) > 0:
            print(f"assistants: {assistant_ids}")

            for assistant_id in assistant_ids:
                print(f"deleting assistant {assistant_id}")
                await self.client.delete_assistant(assistant_id)

            # Get more
            assistant_ids = await self.get_assistant_ids()


if __name__ == '__main__':
    app = ResourcesCli()
    run(app.main_loop())
