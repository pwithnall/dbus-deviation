#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
#
# Copyright © 2016 Kaloyan Tenchov
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
        actual_output = \
            [(None, 'ast', i[0], i[1]) for i in partial_output]
        self.assertEqual(parser.get_output(), actual_output)

    def test_reserved_struct(self):
        """
        Type code 114 'r' is reserved for use in bindings and implementations
        to represent the general concept of a struct, and must not appear in
        signatures used on D-Bus.
        """
        self.assertOutput(
            "r", [
                ('unknown-type', 'Unknown type ‘r’.'),
            ])

    def test_reserved_dict(self):
        """
        Type code 101 'e' is reserved for use in bindings and implementations
        to represent the general concept of a dict or dict-entry, and must not
        appear in signatures used on D-Bus.
        """
        self.assertOutput(
            "e", [
                ('unknown-type', 'Unknown type ‘e’.'),
            ])

    def test_reserved_maybe(self):
        """
        Reserved for a 'maybe' type compatible with the one in GVariant, and
        must not appear in signatures used on D-Bus.
        """
        self.assertOutput(
            "m", [
                ('unknown-type', 'Unknown type ‘m’.'),
            ])

    def test_reserved_star(self):
        """
        Reserved for use in bindings/implementations to represent any single
        complete type, and must not appear in signatures used on D-Bus.
        """
        self.assertOutput(
            "*", [
                ('unknown-type', 'Unknown type ‘*’.'),
            ])

    def test_reserved_question_mark(self):
        """
        Reserved for use in bindings/implementations to represent any basic
        type, and must not appear in signatures used on D-Bus.
        """
        self.assertOutput(
            "?", [
                ('unknown-type', 'Unknown type ‘?’.'),
            ])

    def test_reserved_other_1(self):
        """
        Reserved for internal use by bindings/implementations, and must not
        appear in signatures used on D-Bus.
        """
        self.assertOutput(
            "@", [
                ('unknown-type', 'Unknown type ‘@’.'),
            ])

    def test_reserved_other_2(self):
        self.assertOutput(
            "&", [
                ('unknown-type', 'Unknown type ‘&’.'),
            ])

    def test_reserved_other_3(self):
        self.assertOutput(
            "^", [
                ('unknown-type', 'Unknown type ‘^’.'),
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
        (parser, type_signature) = _test_parser(signature)
        self.assertEqual(parser.get_output(), [])
        actual_signature = str(type_signature)
        self.assertEqual(signature, actual_signature)

    def test_uint8(self):
        """8-bit unsigned integer."""
        self.assertParse("y")

    def test_bool(self):
        """Boolean value."""
        self.assertParse("b")

    def test_int16(self):
        """16-bit signed integer."""
        self.assertParse("n")

    def test_uint16(self):
        """16-bit unsigned integer."""
        self.assertParse("q")

    def test_int32(self):
        """32-bit signed integer."""
        self.assertParse("i")

    def test_two_int32(self):
        self.assertParse("ii")

    def test_two_int32_arrays(self):
        self.assertParse("aiai")

    def test_uint32(self):
        """32-bit unsigned integer."""
        self.assertParse("u")

    def test_two_uint32(self):
        self.assertParse("uu")

    def test_int64(self):
        """64-bit signed integer."""
        self.assertParse("x")

    def test_uint64(self):
        """64-bit unsigned integer."""
        self.assertParse("t")

    def test_double(self):
        """IEEE 754 double."""
        self.assertParse("d")

    def test_string(self):
        """UTF-8 string (must be valid UTF-8)."""
        self.assertParse("s")

    def test_object(self):
        """Name of an object instance."""
        self.assertParse("o")

    def test_signature(self):
        """A type signature."""
        self.assertParse("g")

    def test_variant(self):
        """Variant type."""
        self.assertParse("v")

    def test_fd(self):
        """Unix file descriptor."""
        self.assertParse("h")

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
