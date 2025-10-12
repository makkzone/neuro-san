
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

from unittest import TestCase

from neuro_san.internals.interfaces.dictionary_validator import DictionaryValidator
from neuro_san.internals.validation.network.url_network_validator import UrlNetworkValidator

from tests.neuro_san.internals.validation.network.abstract_network_validator_test import AbstractNetworkValidatorTest


class TestUrlNetworkValidator(TestCase, AbstractNetworkValidatorTest):
    """
    Unit tests for UrlNetworkValidator class.
    """

    def create_validator(self) -> DictionaryValidator:
        """
        Creates an instance of the validator
        """
        return UrlNetworkValidator(external_agents=["/math_guy"])

    def test_valid(self):
        """
        Tests a valid network
        """
        super().test_valid(hocon_file="math_guy_passthrough.hocon")

    def test_no_external_network(self):
        """
        Tests a network where at least one of the nodes does not have a listed external network
        """
        validator: DictionaryValidator = self.create_validator()

        # Open a known good network file
        config: Dict[str, Any] = self.restore("math_guy_passthrough.hocon")

        # Invalidate per the test
        config["tools"][0]["tools"][0] = "/invalid_network"

        errors: List[str] = validator.validate(config)
        self.assertEqual(1, len(errors))
