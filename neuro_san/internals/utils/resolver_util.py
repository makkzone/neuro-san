
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
from typing import Tuple
from typing import Type

from leaf_common.config.resolver import Resolver


class ResolverUtil:
    """
    Helper class for creating instances of classes that are referenced by a string.
    """

    @staticmethod
    def create_type(fully_qualified_name: str, install_if_missing: str = None) -> Type[Any]:
        """
        :param fully_qualified_name: The fully qualified name of the class to create
        :param install_if_missing: The pip package to install if the class is not found
        :return: The class referenced (not an instance of the class)
        """
        if not fully_qualified_name:
            return None

        name_split: List[str] = fully_qualified_name.split(".")
        module_name: str = ".".join(name_split[:-1])
        class_name: str = name_split[-1]

        resolver = Resolver()
        class_type: Type[Any] = resolver.resolve_class_in_module(class_name,
                                                                 module_name=module_name,
                                                                 install_if_missing=install_if_missing)
        return class_type

    @staticmethod
    def create_type_tuple(type_list: List[str]) -> Tuple[Type[Any], ...]:
        """
        Creates a tuple of class types for use in isinstance(obj, <tuple_of_types>)
        situations.

        :param type_list: A list of fully qualified names of the types to create
                          (not class instances) to the string name of the package to install
                          if the class is not found.
        :return: A tuple of the class types that could be resolved.
                Can return an empty tuple if nothing in the type_list could be resolved
        """

        if not type_list:
            return ()

        tuple_list: List[Type[Any]] = []
        for class_name in type_list:

            # Try to resolve the single type and append to list if we get it.
            one_type: Type[Any] = ResolverUtil.create_type(class_name, install_if_missing=None)
            if one_type is not None:
                tuple_list.append(one_type)

        return tuple(tuple_list)

    @staticmethod
    def create_type_tuple_from_dict(type_dict: Dict[str, str]) -> Tuple[Type[Any], ...]:
        """
        Creates a tuple of class types for use in isinstance(obj, <tuple_of_types>)
        situations.

        :param type_dict: A dictionary of fully qualified names of the types to create
                          (not class instances) to the string name of the package to install
                          if the class is not found.  The values in the dictionary can be
                          empty strings, in which case no warning as to what package to install
                          will be given.
        :return: A tuple of the class types that could be resolved.
                Can return an empty tuple if nothing in the type_dict could be resolved
        """

        if not type_dict:
            return ()

        tuple_list: List[Type[Any]] = []
        for class_name, install_if_missing in type_dict.items():

            # Allow for values that are empty strings
            if install_if_missing is not None and len(install_if_missing) == 0:
                install_if_missing = None

            # Try to resolve the single type and append to list if we get it.
            one_type: Type[Any] = ResolverUtil.create_type(class_name, install_if_missing)
            if one_type is not None:
                tuple_list.append(one_type)

        return tuple(tuple_list)
