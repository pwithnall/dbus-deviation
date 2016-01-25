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

from dbusapi import ast


class TypeParser(object):

    """
    Parse a D-Bus type string.

    This validates the string, but not exceedingly strictly..
    """

    def __init__(self, signature):
        """
        Construct a new TypeParser.

        Args:
            signature: A D-Bus type string.
        """
        self.signature = signature
        self._output = []
        self._index = 0

    @staticmethod
    def get_output_codes():
        """Return a list of all possible output codes."""
        # FIXME: Hard-coded for the moment.
        return [
            'unknown-type',
        ]

    def _issue_output(self, code, message):
        """Append a message to the parser output."""
        self._output.append((code, message))

    def get_output(self):
        """Return a list of all logged parser messages."""
        return self._output

    def _get_next_character(self):
        """Return the next character from the signature."""
        if self._index < len(self.signature):
            character = self.signature[self._index]
            self._index += 1
        else:
            character = None
        return character

    def _parse_one(self, character):
        """Parse one character of a signature."""
        if character == "y":
            return ast.Byte()
        elif character == "b":
            return ast.Boolean()
        elif character == "n":
            return ast.Int16()
        elif character == "q":
            return ast.UInt16()
        elif character == "i":
            return ast.Int32()
        elif character == "u":
            return ast.UInt32()
        elif character == "x":
            return ast.Int64()
        elif character == "t":
            return ast.UInt64()
        elif character == "d":
            return ast.Double()
        elif character == "s":
            return ast.String()
        elif character == "o":
            return ast.ObjectPath()
        elif character == "g":
            return ast.Signature()
        elif character == "v":
            return ast.Variant()
        elif character == "h":
            return ast.UnixFD()
        elif character == "a":
            res = ast.Array()
            character = self._get_next_character()
            if not character:
                self._issue_output('invalid-type',
                                   'Incomplete array declaration.')
                return None
            one_type = self._parse_one(character)
            if not one_type:
                # Invalid member type
                return None
            res.members.append(one_type)
            return res
        elif character == "(":
            res = ast.Struct()
            while True:
                character = self._get_next_character()
                if not character:
                    self._issue_output('invalid-type',
                                       'Incomplete structure declaration.')
                    return None
                if character == ")":
                    break
                one_type = self._parse_one(character)
                if not one_type:
                    # Invalid member type
                    return None
                res.members.append(one_type)
            return res
        elif character == "{":
            res = ast.DictEntry()
            while True:
                character = self._get_next_character()
                if not character:
                    self._issue_output('invalid-type',
                                       'Incomplete dictionary declaration.')
                    return None
                if character == "}":
                    break
                one_type = self._parse_one(character)
                if not one_type:
                    # Invalid member type
                    return None
                if len(res.members) >= 2:
                    self._issue_output('invalid-type',
                                       'Invalid dictionary declaration.')
                    return None
                res.members.append(one_type)
            return res
        else:
            self._issue_output('unknown-type',
                               'Unknown type ‘%s’.' % character)
            return None

    def parse(self):
        """
        Parse the type string and build an AST.

        Returns:
            A non-empty list of types.

            If parsing fails, None is returned.
        """
        self._output = []
        self._index = 0

        out = ast.Signature()
        while True:
            character = self._get_next_character()
            if not character:
                break

            one_type = self._parse_one(character)
            if not one_type:
                # Invalid type
                break

            out.members.append(one_type)

        # Squash output on error.
        if self._output:
            return None

        return out
