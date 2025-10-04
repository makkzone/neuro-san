
import os
from typing import Any, Dict

from pyparsing.exceptions import ParseException
from pyparsing.exceptions import ParseSyntaxException

from leaf_common.config.file_of_class import FileOfClass
from leaf_common.persistence.easy.easy_hocon_persistence import EasyHoconPersistence

from neuro_san import DEPLOY_DIR


class ExternalCredentialsProvider:

    credentials_table: Dict[str, Any] = None
    # This will be populated by load_credentials()

    @classmethod
    def load_credentials(cls):
        credentials_file: str = os.environ.get("MCP_CREDENTIALS_FILE")
        if credentials_file is None:
            # No env var, so fallback to what is coded in this repo.
            credentials_file = DEPLOY_DIR.get_file_in_basis("mcp_credentials.hocon")
            if credentials_file.endswith(".hocon"):
                hocon = EasyHoconPersistence()
                try:
                    endpoints = hocon.restore(file_reference=credentials_file)
                except (ParseException, ParseSyntaxException) as exception:
                    message: str = f"""
        There was an error parsing MCP credentials file "{credentials_file}".
        See the accompanying ParseException (above) for clues as to what might be
        syntactically incorrect in that file.
        """
                    raise ParseException(message) from exception
            else:
                try:
                    with open(credentials_file, "r", encoding="utf-8") as json_file:
                        endpoints = json.load(json_file)
                except FileNotFoundError:
                    # Use the common verbiage below
                    one_manifest = None
                except json.decoder.JSONDecodeError as exception:
                    message: str = f"""
        There was an error parsing MCP credentials file "{credentials_file}".
        See the accompanying JSONDecodeError exception (above) for clues as to what might be
        syntactically incorrect in that file.
        """
                    raise ParseException(message) from exception
        if endpoints is None:
            return
        cls.credentials_table = {}
        for endpoint in endpoints.get("table", []):
            key = endpoint.get("endpoint", None)
            headers = endpoint.get("credentials_header", None)
            if key and headers:
                cls.credentials_table[key] = headers

    @classmethod
    def get_credentials(cls, client: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract credentials from a client configuration dictionary.

        :param client: A dictionary containing client configuration.
        :return: A dictionary with extracted credentials.
        """
        if cls.credentials_table is None:
            cls.load_credentials()

        print(f"Credentials table loaded: {cls.credentials_table}")

        if client is None:
            return None

        client_endpoint = client.get("endpoint", None)
        if client_endpoint is None or len(client_endpoint) == 0:
            return None

        creds_header: Dict[str, Any] = cls.credentials_table.get(client_endpoint, None)
        return creds_header
