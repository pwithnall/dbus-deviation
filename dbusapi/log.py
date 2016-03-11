# -*- coding: utf-8 -*-
#
# Copyright © 2015, 2016 Collabora Ltd.
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.


"""
An implementation of a base logging class.
"""


class Log(object):

    """Base logging class."""

    def __init__(self):
        """Construct a new Log"""
        self.issues = []
        self.issue_codes = set()
        self.domain = 'default'

    def register_issue_code(self, code):
        """
        Register a new issue code.

        Duplicate codes will be silently ignored.

        Args:
            code: str, an issue code, for example `unknown-node`
        """
        self.issue_codes.add(code)

    def log_issue(self, code, message):
        """
        Log a new issue.

        Args:
            code: str, A registered code for that issue.
            message: str, A message describing the issue.
        """
        assert code in self.issue_codes
        self.issues.append(self._create_entry(code, message))

    # pylint: disable=no-self-use
    def _create_entry(self, code, message):
        return None, self.domain, code, message

    def clear(self):
        """Clear the issue list."""
        self.issues = []
