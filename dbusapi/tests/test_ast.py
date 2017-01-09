#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright © 2015 Collabora Ltd.
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
Unit tests for dbusapi.ast
"""


# pylint: disable=missing-docstring


from dbusapi import ast
from dbusapi.types import TypeSignature
import unittest


# pylint: disable=too-many-public-methods
class TestAstNames(unittest.TestCase):
    """Test AST node name generation."""

    def test_interface(self):
        iface = ast.Interface('Some.Interface')
        self.assertEqual(iface.format_name(), 'Some.Interface')

    def test_property(self):
        prop = ast.Property('AProperty', 's', ast.Property.ACCESS_READ)
        ast.Interface('Some.Interface', {}, {
            'AProperty': prop,
        })
        self.assertEqual(prop.format_name(), 'Some.Interface.AProperty')

    def test_property_unparented(self):
        prop = ast.Property('AProperty', 's', ast.Property.ACCESS_READ)
        self.assertEqual(prop.format_name(), 'AProperty')

    def test_method(self):
        method = ast.Method('AMethod', [])
        ast.Interface('Some.Interface', {
            'AMethod': method,
        })
        self.assertEqual(method.format_name(), 'Some.Interface.AMethod')

    def test_method_unparented(self):
        method = ast.Method('AMethod', [])
        self.assertEqual(method.format_name(), 'AMethod')

    def test_signal(self):
        signal = ast.Signal('SomeSignal', [])
        ast.Interface('Some.Interface', {}, {}, {
            'SomeSignal': signal,
        })
        self.assertEqual(signal.format_name(), 'Some.Interface.SomeSignal')

    def test_signal_unparented(self):
        signal = ast.Signal('SomeSignal', [])
        self.assertEqual(signal.format_name(), 'SomeSignal')

    def test_argument(self):
        arg = ast.Argument('self', ast.Argument.DIRECTION_IN, 's')
        ast.Method('ParentMethod', [arg])
        self.assertEqual(arg.format_name(),
                         '0 (‘self’) of method ‘ParentMethod’')

    def test_argument_unparented(self):
        arg = ast.Argument('self', ast.Argument.DIRECTION_IN, 's')
        self.assertEqual(arg.format_name(), '‘self’')

    def test_argument_unnamed(self):
        arg = ast.Argument(None, ast.Argument.DIRECTION_IN, 's')
        ast.Method('ParentMethod', [arg])
        self.assertEqual(arg.format_name(), '0 of method ‘ParentMethod’')

    # pylint: disable=invalid-name
    def test_argument_unnamed_unparented(self):
        arg = ast.Argument(None, ast.Argument.DIRECTION_IN, 's')
        self.assertEqual(arg.format_name(), 'unnamed')

    def test_annotation_interface(self):
        annotation = ast.Annotation('SomeAnnotation', 'value')
        ast.Interface('Some.Interface', {}, {}, {}, {
            'SomeAnnotation': annotation,
        })
        self.assertEqual(annotation.format_name(),
                         'SomeAnnotation of ‘Some.Interface’')

    def test_annotation_property(self):
        annotation = ast.Annotation('SomeAnnotation', 'value')
        prop = ast.Property('AProperty', 's', ast.Property.ACCESS_READ, {
            'SomeAnnotation': annotation,
        })
        ast.Interface('Some.Interface', {}, {
            'AProperty': prop,
        })
        self.assertEqual(annotation.format_name(),
                         'SomeAnnotation of ‘Some.Interface.AProperty’')

    def test_annotation_method(self):
        annotation = ast.Annotation('SomeAnnotation', 'value')
        method = ast.Method('AMethod', [], {
            'SomeAnnotation': annotation,
        })
        ast.Interface('Some.Interface', {
            'AMethod': method,
        })
        self.assertEqual(annotation.format_name(),
                         'SomeAnnotation of ‘Some.Interface.AMethod’')

    def test_annotation_signal(self):
        annotation = ast.Annotation('SomeAnnotation', 'value')
        signal = ast.Signal('ASignal', [], {
            'SomeAnnotation': annotation,
        })
        ast.Interface('Some.Interface', {}, {}, {
            'ASignal': signal,
        })
        self.assertEqual(annotation.format_name(),
                         'SomeAnnotation of ‘Some.Interface.ASignal’')

    def test_annotation_argument(self):
        annotation = ast.Annotation('SomeAnnotation', 'value')
        arg = ast.Argument('Argument', ast.Argument.DIRECTION_IN, 's', {
            'SomeAnnotation': annotation,
        })
        method = ast.Method('AMethod', [arg])
        ast.Interface('Some.Interface', {
            'AMethod': method,
        })
        self.assertEqual(annotation.format_name(),
                         'SomeAnnotation of ‘0 (‘Argument’)'
                         ' of method ‘Some.Interface.AMethod’’')

    def test_annotation_unparented(self):
        annotation = ast.Annotation('SomeAnnotation', 'value')
        self.assertEqual(annotation.format_name(), 'SomeAnnotation')


# pylint: disable=too-many-public-methods
class TestAstParenting(unittest.TestCase):
    """Test AST node parenting."""

    def test_property(self):
        annotation = ast.Annotation('SomeAnnotation', 'value')
        self.assertEqual(annotation.parent, None)

        prop = ast.Property('AProperty', 's', ast.Property.ACCESS_READ, {
            'SomeAnnotation': annotation,
        })
        self.assertEqual(prop.interface, None)
        self.assertEqual(annotation.parent, prop)

        iface = ast.Interface('Some.Interface', {}, {
            'AProperty': prop,
        })
        self.assertEqual(prop.interface, iface)

    def test_method(self):
        annotation = ast.Annotation('SomeAnnotation', 'value')
        self.assertEqual(annotation.parent, None)

        method = ast.Method('AMethod', [], {
            'SomeAnnotation': annotation,
        })
        self.assertEqual(method.interface, None)
        self.assertEqual(annotation.parent, method)

        iface = ast.Interface('Some.Interface', {
            'AMethod': method,
        })
        self.assertEqual(method.interface, iface)

    def test_signal(self):
        annotation = ast.Annotation('SomeAnnotation', 'value')
        self.assertEqual(annotation.parent, None)

        signal = ast.Signal('ASignal', [], {
            'SomeAnnotation': annotation,
        })
        self.assertEqual(signal.interface, None)
        self.assertEqual(annotation.parent, signal)

        iface = ast.Interface('Some.Interface', {}, {
            'ASignal': signal,
        })
        self.assertEqual(signal.interface, iface)

    def test_argument(self):
        annotation = ast.Annotation('SomeAnnotation', 'value')
        self.assertEqual(annotation.parent, None)

        arg = ast.Argument('SomeArgument', ast.Argument.DIRECTION_IN, 's', {
            'SomeAnnotation': annotation,
        })
        self.assertEqual(arg.parent, None)
        self.assertEqual(arg.index, -1)
        self.assertEqual(annotation.parent, arg)

        method = ast.Method('AMethod', [arg])
        self.assertEqual(arg.parent, method)
        self.assertEqual(arg.index, 0)


class TestAstTraversal(unittest.TestCase):
    """Test AST traversal."""

    def test_walk(self):
        annotation = ast.Annotation('SomeAnnotation', 'value')
        method = ast.Method('AMethod', [], {
            'SomeAnnotation': annotation,
        })
        iface = ast.Interface('Some.Interface', {
            'AMethod': method,
        })

        children = [node for node in iface.walk()]
        self.assertEquals(len(children), 2)
        self.assertEquals(children[0], method)
        self.assertEquals(children[1], annotation)


class TestAstSignatures(unittest.TestCase):
    """Test AST node signature parsing."""

    def test_property(self):
        prop = ast.Property('AProperty', 's', ast.Property.ACCESS_READ)
        self.assertIsInstance(prop.type, TypeSignature)
        self.assertEqual(str(prop.type), 's')

    def test_argument(self):
        arg = ast.Argument('self', ast.Argument.DIRECTION_IN, 's')
        self.assertIsInstance(arg.type, TypeSignature)
        self.assertEqual(str(arg.type), 's')


class TestAstLogging(unittest.TestCase):
    """Test error handling in AST"""

    def test_duplicate(self):
        method = ast.Method('AMethod', [])
        iface = ast.Interface('Some.Interface', {
            'AMethod': method,
        })
        self.assertListEqual(iface.log.issues, [])
        duplicate_method = ast.Method('AMethod', [])
        iface.add_child(duplicate_method)
        self.assertListEqual(
            iface.log.issues,
            [(None,
              'ast',
              'duplicate-method',
              'Duplicate method definition ‘Some.Interface.AMethod’.')])


if __name__ == '__main__':
    # Run test suite
    unittest.main()
