#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
#
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
Unit tests for dbusapi.typeformatter
"""


from dbusapi.typeformatter import BasicTypeFormatter
from dbusapi import types
import unittest


class TestBasicFormatterNormal(unittest.TestCase):
    """Test normal formatting of types with the BasicTypeFormatter."""

    # pylint: disable=invalid-name
    def assertFormat(self, type_instance, formatted):  # noqa
        formatter = BasicTypeFormatter()
        self.assertEqual(formatter.format(type_instance), formatted)

    def test_basic_types(self):
        basic_type_map = {
            types.Byte: 'Byte',
            types.Boolean: 'Boolean',
            types.Int16: 'Int16',
            types.UInt16: 'UInt16',
            types.Int32: 'Int32',
            types.UInt32: 'UInt32',
            types.Int64: 'Int64',
            types.UInt64: 'UInt64',
            types.Double: 'Double',
            types.String: 'String',
            types.ObjectPath: 'Object Path',
            types.Signature: 'Signature',
            types.Variant: 'Variant',
            types.UnixFD: 'Unix FD',
        }

        for k, v in basic_type_map.items():
            self.assertFormat(k(), v)

    def test_array(self):
        type_instance = types.Array()
        type_instance.members.append(types.Byte())
        self.assertFormat(type_instance, 'Array of [Byte]')

    def test_struct(self):
        type_instance = types.Struct()
        type_instance.members.append(types.String())
        type_instance.members.append(types.String())
        type_instance.members.append(types.UInt16())
        self.assertFormat(type_instance, 'Struct of (String, String, UInt16)')

    def test_dict(self):
        dict_instance = types.DictEntry()
        dict_instance.members.append(types.String())
        dict_instance.members.append(types.Variant())
        array_instance = types.Array()
        array_instance.members.append(dict_instance)

        self.assertFormat(array_instance, 'Dict of {String: Variant}')

    def test_invalid_dict(self):
        """Test that a bare DictEntry (not in an Array) is not formatted"""
        dict_instance = types.DictEntry()
        dict_instance.members.append(types.String())
        dict_instance.members.append(types.Variant())

        formatter = BasicTypeFormatter()

        with self.assertRaises(AssertionError):
            formatter.format(dict_instance)

    def test_something_long(self):
        type_signature = types.TypeSignature()
        type_signature.members.append(types.Int32())
        type_signature.members.append(types.Int32())
        type_signature.members.append(types.Double())
        type_signature.members.append(types.Double())
        type_signature.members.append(types.Double())
        struct = types.Struct()
        struct.members.append(types.Int32())
        struct.members.append(types.Double())
        struct.members.append(types.Double())
        type_signature.members.append(struct)

        self.assertFormat(type_signature,
                          'Int32, Int32, Double, Double, Double, '
                          'Struct of (Int32, Double, Double)')

    def test_nested_structs(self):
        s1 = types.Struct()
        s1.members.append(types.Int32())
        s1.members.append(types.Int32())
        s2 = types.Struct()
        s2.members.append(types.UInt32())
        s2.members.append(types.UInt32())
        s3 = types.Struct()
        s3.members.append(s1)
        s3.members.append(s2)

        self.assertFormat(s3, 'Struct of ('
                              'Struct of (Int32, Int32), '
                              'Struct of (UInt32, UInt32))')

    def test_type_signature(self):
        signature = types.TypeSignature()
        signature.members.append(types.String())
        signature.members.append(types.UInt64())
        self.assertFormat(signature, 'String, UInt64')


if __name__ == '__main__':
    # Run test suite
    unittest.main()
