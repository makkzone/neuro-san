
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
from neuro_san.internals.validation.network.keyword_network_validator import KeywordNetworkValidator

from tests.neuro_san.internals.validation.network.abstract_network_validator_test import AbstractNetworkValidatorTest


class TestKeywordNetworkValidator(TestCase, AbstractNetworkValidatorTest):
    """
    Unit tests for KeywordNetworkValidator class.
    """

    def create_validator(self) -> DictionaryValidator:
        """
        Creates an instance of the validator
        """
        return KeywordNetworkValidator()

    def test_no_instructions(self):
        """
        Tests a network where at least one of the nodes does not have instructions
        """
        validator: DictionaryValidator = self.create_validator()

        # Open a known good network file
        config: Dict[str, Any] = self.restore("hello_world.hocon")

        # Invalidate per the test
        config["tools"][0]["instructions"] = ""

        errors: List[str] = validator.validate(config)
        self.assertEqual(1, len(errors))
