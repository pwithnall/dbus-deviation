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
Unit tests for dbusapi.ast
"""


# pylint: disable=missing-docstring


from dbusapi import ast
import unittest


# pylint: disable=too-many-public-methods
class TestAstNames(unittest.TestCase):
    """Test AST node name generation."""

    def test_interface(self):
        iface = ast.Interface('SomeInterface')
        self.assertEqual(iface.format_name(), 'SomeInterface')

    def test_property(self):
        prop = ast.Property('AProperty', 's', ast.Property.ACCESS_READ)
        iface = ast.Interface('SomeInterface', {}, {
            'AProperty': prop,
        })
        self.assertEqual(prop.format_name(), 'SomeInterface.AProperty')

    def test_property_unparented(self):
        prop = ast.Property('AProperty', 's', ast.Property.ACCESS_READ)
        self.assertEqual(prop.format_name(), 'AProperty')

    def test_method(self):
        method = ast.Method('AMethod', [])
        iface = ast.Interface('SomeInterface', {
            'AMethod': method,
        })
        self.assertEqual(method.format_name(), 'SomeInterface.AMethod')

    def test_method_unparented(self):
        method = ast.Method('AMethod', [])
        self.assertEqual(method.format_name(), 'AMethod')

    def test_signal(self):
        signal = ast.Signal('SomeSignal', [])
        iface = ast.Interface('SomeInterface', {}, {}, {
            'SomeSignal': signal,
        })
        self.assertEqual(signal.format_name(), 'SomeInterface.SomeSignal')

    def test_signal_unparented(self):
        signal = ast.Signal('SomeSignal', [])
        self.assertEqual(signal.format_name(), 'SomeSignal')

    def test_argument(self):
        arg = ast.Argument('self', ast.Argument.DIRECTION_IN, 's')
        method = ast.Method('ParentMethod', [arg])
        self.assertEqual(arg.format_name(),
                         '0 (‘self’) of method ‘ParentMethod’')

    def test_argument_unparented(self):
        arg = ast.Argument('self', ast.Argument.DIRECTION_IN, 's')
        self.assertEqual(arg.format_name(), '‘self’')

    def test_argument_unnamed(self):
        arg = ast.Argument(None, ast.Argument.DIRECTION_IN, 's')
        method = ast.Method('ParentMethod', [arg])
        self.assertEqual(arg.format_name(), '0 of method ‘ParentMethod’')

    # pylint: disable=invalid-name
    def test_argument_unnamed_unparented(self):
        arg = ast.Argument(None, ast.Argument.DIRECTION_IN, 's')
        self.assertEqual(arg.format_name(), 'unnamed')

    def test_annotation_interface(self):
        annotation = ast.Annotation('SomeAnnotation', 'value')
        iface = ast.Interface('SomeInterface', {}, {}, {}, {
            'SomeAnnotation': annotation,
        })
        self.assertEqual(annotation.format_name(),
                         'SomeAnnotation of ‘SomeInterface’')

    def test_annotation_property(self):
        annotation = ast.Annotation('SomeAnnotation', 'value')
        prop = ast.Property('AProperty', 's', ast.Property.ACCESS_READ, {
            'SomeAnnotation': annotation,
        })
        iface = ast.Interface('SomeInterface', {}, {
            'AProperty': prop,
        })
        self.assertEqual(annotation.format_name(),
                         'SomeAnnotation of ‘SomeInterface.AProperty’')

    def test_annotation_method(self):
        annotation = ast.Annotation('SomeAnnotation', 'value')
        method = ast.Method('AMethod', [], {
            'SomeAnnotation': annotation,
        })
        iface = ast.Interface('SomeInterface', {
            'AMethod': method,
        })
        self.assertEqual(annotation.format_name(),
                         'SomeAnnotation of ‘SomeInterface.AMethod’')

    def test_annotation_signal(self):
        annotation = ast.Annotation('SomeAnnotation', 'value')
        signal = ast.Signal('ASignal', [], {
            'SomeAnnotation': annotation,
        })
        iface = ast.Interface('SomeInterface', {}, {}, {
            'ASignal': signal,
        })
        self.assertEqual(annotation.format_name(),
                         'SomeAnnotation of ‘SomeInterface.ASignal’')

    def test_annotation_argument(self):
        annotation = ast.Annotation('SomeAnnotation', 'value')
        arg = ast.Argument('Argument', ast.Argument.DIRECTION_IN, 's', {
            'SomeAnnotation': annotation,
        })
        method = ast.Method('AMethod', [arg])
        iface = ast.Interface('SomeInterface', {
            'AMethod': method,
        })
        self.assertEqual(annotation.format_name(),
                         'SomeAnnotation of ‘0 (‘Argument’)'
                         ' of method ‘SomeInterface.AMethod’’')

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

        iface = ast.Interface('SomeInterface', {}, {
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

        iface = ast.Interface('SomeInterface', {
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

        iface = ast.Interface('SomeInterface', {}, {
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
        iface = ast.Interface('SomeInterface', {
            'AMethod': method,
        })

        children = [node for node in iface.walk()]
        self.assertEquals(len(children), 2)
        self.assertEquals(children[0], method)
        self.assertEquals(children[1], annotation)


class TestAstLogging(unittest.TestCase):
    """Test error handling in AST"""

    def test_duplicate(self):
        method = ast.Method('AMethod', [])
        iface = ast.Interface('SomeInterface', {
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
              'Duplicate method definition ‘SomeInterface.AMethod’.')])


if __name__ == '__main__':
    # Run test suite
    unittest.main()
