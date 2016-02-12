#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
#
# Copyright © 2015 Collabora Ltd.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""TODO"""

from dbusapi.ast import parse, Loggable


class InterfaceParser(object):

    """
    Parse a D-Bus introspection XML file.

    Deprecated: use `ast.parse` directly

    This validates the file, but not exceedingly strictly. It is a pragmatic
    parser, designed for use by the InterfaceComparator rather than more
    general code. It ignores certain common extensions found in introspection
    XML files, such as documentation elements, but will fail on other
    unrecognised elements.
    """

    def __init__(self, filename):
        """
        Construct a new InterfaceParser.

        Deprecated: use `ast.parse` directly

        Args:
            filename: path to the XML introspection file to parse
        """
        self._filename = filename
        self._output = []

    @staticmethod
    def get_output_codes():
        """
        Return a list of all possible output codes.

        Deprecated: use `Loggable.get_error_codes` instead
        """
        return Loggable.get_error_codes()

    def get_output(self):
        """Return a list of all logged parser messages."""
        return self._output

    def parse(self):
        """
        Parse the introspection XML file and build an AST.

        Deprecated: use `ast.parse` directly

        Returns:
            A non-empty dict of interfaces in the file, mapping each interface
            name to an ast.Interface instance.
            If parsing fails, None is returned.
        """
        interfaces, self._output = parse(self._filename)
        # Squash output on error.
        if len(self._output) != 0:
            return None

        return interfaces
