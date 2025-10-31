
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
from neuro_san.service.main_loop.server_main_loop import ServerMainLoop


# Backwards compatibility entry point
if __name__ == '__main__':
    print("""
WARNING: The class:
    neuro_san.service.agent_main_loop.AgentMainLoop
... has moved to be ...
    neuro_san.service.main_loop.server_main_loop.ServerMainLoop
Please update your Neuro SAN agent server start-up scripts accordingly.
    """)
    ServerMainLoop().main_loop()
