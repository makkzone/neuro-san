
# Copyright (C) 2019-2023 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
#
# This software is a trade secret, and contains proprietary and confidential
# materials of Cognizant Digital Business Evolutionary AI.
# Cognizant Digital Business prohibits the use, transmission, copying,
# distribution, or modification of this software outside of the
# Cognizant Digital Business EAI organization.
#
# END COPYRIGHT

from enum import Enum


# class syntax
class Permission(Enum):
    """
    Different kinds of permissions on our objects
    that we will request authorization for.
    """
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
