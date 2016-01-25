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

"""
Unit tests for dbusapi.typeparser
"""


from dbusapi.typeparser import TypeParser
import unittest


def _test_parser(signature):
    """Build a TypeParser for a signature and parse it."""
    parser = TypeParser(signature)
    types = parser.parse()
    return parser, types


class TestParserErrors(unittest.TestCase):
    """Test error handling in the TypeParser."""

    # pylint: disable=invalid-name
    def assertOutput(self, signature, partial_output):  # noqa
        (parser, types) = _test_parser(signature)
        self.assertEqual(types, None)
        actual_output = [(i[0], i[1]) for i in partial_output]
        self.assertEqual(parser.get_output(), actual_output)

    def test_unknown_type(self):
        self.assertOutput(
            "?", [
                ('unknown-type', 'Unknown type ‘?’.'),
            ])

    def test_incomplete(self):
        self.assertOutput(
            "aa", [
                ('invalid-type', 'Incomplete array declaration.'),
            ])

    def test_incomplete2(self):
        self.assertOutput(
            "(ii", [
                ('invalid-type', 'Incomplete structure declaration.'),
            ])

    def test_incomplete3(self):
        self.assertOutput(
            "ii)", [
                ('unknown-type', 'Unknown type ‘)’.'),
            ])

    def test_incomplete4(self):
        self.assertOutput(
            "a{suu}", [
                ('invalid-type', 'Invalid dictionary declaration.'),
            ])

    def test_incomplete5(self):
        self.assertOutput(
            "a{su", [
                ('invalid-type', 'Incomplete dictionary declaration.'),
            ])

    def test_incomplete6(self):
        self.assertOutput(
            "a{s", [
                ('invalid-type', 'Incomplete dictionary declaration.'),
            ])


class TestParserNormal(unittest.TestCase):
    """Test normal parsing of unusual input in the TypeParser."""

    # pylint: disable=invalid-name
    def assertParse(self, signature):  # noqa
        (parser, type) = _test_parser(signature)
        self.assertEqual(parser.get_output(), [])
        actual_signature = str(type)
        self.assertEqual(signature, actual_signature)

    def test_int32(self):
        self.assertParse("i")

    def test_two_int32(self):
        self.assertParse("ii")

    def test_two_int32_arrays(self):
        self.assertParse("aiai")

    def test_uint32(self):
        self.assertParse("u")

    def test_two_uint32(self):
        self.assertParse("uu")

    def test_array_int32(self):
        self.assertParse("ai")

    def test_array_array_int32(self):
        self.assertParse("aai")

    def test_array_uint32(self):
        self.assertParse("au")

    def test_array_variant(self):
        self.assertParse("av")

    def test_struct_ints(self):
        self.assertParse("(iii)")

    def test_two_structs(self):
        self.assertParse("(ii)(ii)")

    def test_struct_struct_ints(self):
        self.assertParse("(i(ii))")

    def test_struct_variant(self):
        self.assertParse("(v)")

    def test_struct_ius(self):
        self.assertParse("(ius)")

    def test_array_struct_ints(self):
        self.assertParse("a(ii)")

    def test_array_dict(self):
        self.assertParse("a{us}")

    def test_array_dict2(self):
        self.assertParse("a{us}i")


if __name__ == '__main__':
    # Run test suite
    unittest.main()
