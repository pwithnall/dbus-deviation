#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
#
# Copyright © 2016 Kaloyan Tenchov
# Copyright © 2017 Philip Withnall
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
            [(None, 'types', i[0], i[1]) for i in partial_output]
        self.assertEqual(parser.get_output(), actual_output)

    def test_reserved(self):
        """
        Type code 114 'r' is reserved for use in bindings and implementations
        to represent the general concept of a struct, and must not appear in
        signatures used on D-Bus.

        Similarly for the other type strings here.

        https://dbus.freedesktop.org/doc/dbus-specification.html#idm399
        """
        vectors = [
            'r', 'e', 'm', '*', '?', '@', '&', '^'
        ]
        for type_string in vectors:
            # Unfortunately we can’t use TestCase.subTest here until we depend
            # on Python 3.4 at a minimum.
            self.assertOutput(type_string, [
                ('reserved-type',
                 'Reserved type ‘%s’ must not be used in signatures on '
                 'D-Bus.' % type_string),
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

    def test_invalid_array(self):
        self.assertOutput(
            'a!', [
                ('unknown-type', 'Unknown type ‘!’.'),
            ]
        )

    def test_empty(self):
        self.assertOutput(
            "", [
                ('invalid-type', 'Empty type string.'),
            ]
        )

    def test_empty_tuple(self):
        self.assertOutput(
            '()', [
                ('invalid-type', 'Incomplete structure declaration.'),
            ]
        )

    def test_invalid_tuple(self):
        self.assertOutput(
            '(!', [
                ('unknown-type', 'Unknown type ‘!’.'),
            ]
        )

    def test_empty_dict(self):
        self.assertOutput(
            '{}', [
                ('invalid-type', 'Incomplete dictionary declaration.'),
            ]
        )

    def test_invalid_dict(self):
        self.assertOutput(
            '{!', [
                ('unknown-type', 'Unknown type ‘!’.'),
            ]
        )

    def test_underfilled_dict(self):
        self.assertOutput(
            '{s}', [
                ('invalid-type', 'Incomplete dictionary declaration.'),
            ]
        )

    def test_overfilled_dict(self):
        self.assertOutput(
            '{sss}', [
                ('invalid-type', 'Invalid dictionary declaration.'),
            ]
        )


class TestParserNormal(unittest.TestCase):
    """Test normal parsing of unusual input in the TypeParser."""

    # pylint: disable=invalid-name
    def assertParse(self, signature):  # noqa
        (parser, type_signature) = _test_parser(signature)
        self.assertEqual(parser.get_output(), [])
        actual_signature = str(type_signature)
        self.assertEqual(signature, actual_signature)

    def test_parse_valid(self):
        vectors = [
            'y', 'b', 'n', 'q', 'i', 'ii', 'aiai', 'u', 'uu', 'x', 't', 'd',
            's', 'o', 'g', 'v', 'h', 'ai', 'aai', 'au', 'av', '(iii)',
            '(ii)(ii)', '(i(ii))', '(v)', '(ius)', 'a(ii)', 'a{us}', 'a{us}i'
        ]
        for type_string in vectors:
            # Unfortunately we can’t use TestCase.subTest here until we depend
            # on Python 3.4 at a minimum.
            self.assertParse(type_string)


class TestParserOutputCodes(unittest.TestCase):
    """Test the output codes from TypeParser."""

    def test_unique(self):
        codes = TypeParser.get_output_codes()
        self.assertEqual(len(codes), len(set(codes)))

    def test_non_empty(self):
        codes = TypeParser.get_output_codes()
        self.assertNotEqual(codes, [])


if __name__ == '__main__':
    # Run test suite
    unittest.main()
