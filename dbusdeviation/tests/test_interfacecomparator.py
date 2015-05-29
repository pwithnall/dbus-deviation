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
Unit tests for dbus-interface-diff
"""


# pylint: disable=missing-docstring


from dbusapi.interfaceparser import InterfaceParser
from dbusdeviation.interfacecomparator import InterfaceComparator
import os
import tempfile
import unittest


def _create_temp_xml_file(xml):
    """Create a temporary XML file with the given contents."""
    tmp_fd, tmp_name = tempfile.mkstemp(suffix='.xml', text=True)
    xml_fd = os.fdopen(tmp_fd, 'wt')
    xml_fd.write(xml)
    xml_fd.close()

    return tmp_name


# pylint: disable=too-many-public-methods
class TestComparatorErrors(unittest.TestCase):
    """Test log output from InterfaceComparator."""

    def _test_comparator(self, old_xml, new_xml):
        """Build an InterfaceComparator for the two parsed XML snippets."""
        old_tmpfile = _create_temp_xml_file(old_xml)
        new_tmpfile = _create_temp_xml_file(new_xml)

        old_parser = InterfaceParser(old_tmpfile)
        new_parser = InterfaceParser(new_tmpfile)

        old_interfaces = old_parser.parse()
        new_interfaces = new_parser.parse()

        os.unlink(new_tmpfile)
        os.unlink(old_tmpfile)

        self.assertEqual(old_parser.get_output(), [])
        self.assertEqual(new_parser.get_output(), [])

        self.assertNotEqual(old_interfaces, None)
        self.assertNotEqual(new_interfaces, None)

        return InterfaceComparator(old_interfaces, new_interfaces)

    # pylint: disable=invalid-name
    def assertOutput(self, old_xml, new_xml, output):  # noqa
        comparator = self._test_comparator(old_xml, new_xml)
        self.assertEqual(comparator.compare(), output)
        self.assertEqual(comparator.get_output(), output)

    def test_interface_removed(self):
        self.assertOutput(
            "<node><interface name='A'/></node>",
            "<node></node>", [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Interface ‘A’ has been removed.'),
            ])

    def test_interface_added(self):
        self.assertOutput(
            "<node></node>",
            "<node><interface name='A'/></node>", [
                (InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'Interface ‘A’ has been added.'),
            ])

    def test_interface_deprecated(self):
        self.assertOutput(
            "<node><interface name='A'/></node>",
            "<node><interface name='A'>"
            "<annotation name='org.freedesktop.DBus.Deprecated' value='true'/>"
            "</interface></node>", [
                (InterfaceComparator.OUTPUT_INFO,
                 'Node ‘A’ has been deprecated.'),
            ])

    def test_interface_deprecated_explicit(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<annotation name='org.freedesktop.DBus.Deprecated' "
            "value='false'/>"
            "</interface></node>",
            "<node><interface name='A'>"
            "<annotation name='org.freedesktop.DBus.Deprecated' value='true'/>"
            "</interface></node>", [
                (InterfaceComparator.OUTPUT_INFO,
                 'Node ‘A’ has been deprecated.'),
            ])

    def test_interface_undeprecated(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<annotation name='org.freedesktop.DBus.Deprecated' value='true'/>"
            "</interface></node>",
            "<node><interface name='A'/></node>", [
                (InterfaceComparator.OUTPUT_INFO,
                 'Node ‘A’ has been un-deprecated.'),
            ])

    def test_interface_undeprecated_explicit(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<annotation name='org.freedesktop.DBus.Deprecated' value='true'/>"
            "</interface></node>",
            "<node><interface name='A'>"
            "<annotation name='org.freedesktop.DBus.Deprecated' "
            "value='false'/>"
            "</interface></node>", [
                (InterfaceComparator.OUTPUT_INFO,
                 'Node ‘A’ has been un-deprecated.'),
            ])

    def test_interface_name_changed(self):
        self.assertOutput(
            "<node><interface name='A'/></node>",
            "<node><interface name='A2'/></node>", [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Interface ‘A’ has been removed.'),
                (InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'Interface ‘A2’ has been added.')
            ])

    def test_method_removed(self):
        self.assertOutput(
            "<node><interface name='A'><method name='M'/></interface></node>",
            "<node><interface name='A'/></node>", [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Method ‘A.M’ has been removed.'),
            ])

    def test_method_added(self):
        self.assertOutput(
            "<node><interface name='A'/></node>",
            "<node><interface name='A'><method name='M'/></interface></node>",
            [
                (InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'Method ‘A.M’ has been added.'),
            ])

    def test_method_name_changed(self):
        self.assertOutput(
            "<node><interface name='A'><method name='M'/></interface></node>",
            "<node><interface name='A'><method name='M2'/></interface></node>",
            [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Method ‘A.M’ has been removed.'),
                (InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'Method ‘A.M2’ has been added.'),
            ])

    def test_method_arg_removed(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<method name='M'><arg type='s' direction='in'/></method>"
            "</interface></node>",
            "<node><interface name='A'><method name='M'/></interface></node>",
            [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Argument 0 of method ‘A.M’ has been removed.'),
            ])

    def test_method_arg_added(self):
        self.assertOutput(
            "<node><interface name='A'><method name='M'/></interface></node>",
            "<node><interface name='A'>"
            "<method name='M'><arg type='s' direction='in'/></method>"
            "</interface></node>",
            [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Argument 0 of method ‘A.M’ has been added.'),
            ])

    def test_method_arg_name_changed(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<method name='M'><arg type='s' name='A' direction='in'/></method>"
            "</interface></node>",
            "<node><interface name='A'>"
            "<method name='M'><arg type='s' name='Z' direction='in'/></method>"
            "</interface></node>",
            [
                (InterfaceComparator.OUTPUT_INFO,
                 'Argument 0 of ‘A.M’ has changed name from ‘A’ to ‘Z’.'),
            ])

    def test_method_arg_type_changed(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<method name='M'><arg type='s' direction='in'/></method>"
            "</interface></node>",
            "<node><interface name='A'>"
            "<method name='M'><arg type='b' direction='in'/></method>"
            "</interface></node>",
            [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Argument 0 of ‘A.M’ has changed type from ‘s’ to ‘b’.'),
            ])

    def test_method_arg_direction_changed(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<method name='M'><arg type='s' direction='in'/></method>"
            "</interface></node>",
            "<node><interface name='A'>"
            "<method name='M'><arg type='s' direction='out'/></method>"
            "</interface></node>",
            [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Argument 0 of ‘A.M’ has changed direction from ‘in’ to '
                 '‘out’.'),
            ])

    def test_method_c_symbol_changed(self):
        self.assertOutput(
            "<node><interface name='A'><method name='M'>"
            "<annotation name='org.freedesktop.DBus.GLib.CSymbol' value='S1'/>"
            "</method></interface></node>",
            "<node><interface name='A'><method name='M'>"
            "<annotation name='org.freedesktop.DBus.GLib.CSymbol' value='S2'/>"
            "</method></interface></node>", [
                (InterfaceComparator.OUTPUT_INFO,
                 'Node ‘A.M’ has changed its C symbol from ‘S1’ to ‘S2’.'),
            ])

    def test_method_no_reply_changed_to_false(self):
        self.assertOutput(
            "<node><interface name='A'><method name='M'>"
            "<annotation name='org.freedesktop.DBus.Method.NoReply' "
            "value='true'/>"
            "</method></interface></node>",
            "<node><interface name='A'><method name='M'>"
            "<annotation name='org.freedesktop.DBus.Method.NoReply' "
            "value='false'/>"
            "</method></interface></node>", [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Node ‘A.M’ has been marked as returning a reply.'),
            ])

    def test_method_no_reply_changed_to_true(self):
        self.assertOutput(
            "<node><interface name='A'><method name='M'/></interface></node>",
            "<node><interface name='A'><method name='M'>"
            "<annotation name='org.freedesktop.DBus.Method.NoReply' "
            "value='true'/>"
            "</method></interface></node>", [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Node ‘A.M’ has been marked as not returning a reply.'),
            ])

    def test_method_no_reply_changed_to_true_explicit(self):
        self.assertOutput(
            "<node><interface name='A'><method name='M'>"
            "<annotation name='org.freedesktop.DBus.Method.NoReply' "
            "value='false'/>"
            "</method></interface></node>",
            "<node><interface name='A'><method name='M'>"
            "<annotation name='org.freedesktop.DBus.Method.NoReply' "
            "value='true'/>"
            "</method></interface></node>", [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Node ‘A.M’ has been marked as not returning a reply.'),
            ])

    def test_property_removed(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<property name='P' type='b' access='readwrite'/>"
            "</interface></node>",
            "<node><interface name='A'/></node>", [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Property ‘A.P’ has been removed.'),
            ])

    def test_property_added(self):
        self.assertOutput(
            "<node><interface name='A'/></node>",
            "<node><interface name='A'>"
            "<property name='P' type='b' access='readwrite'/>"
            "</interface></node>",
            [
                (InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'Property ‘A.P’ has been added.'),
            ])

    def test_property_name_changed(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<property name='P' type='b' access='readwrite'/>"
            "</interface></node>",
            "<node><interface name='A'>"
            "<property name='P2' type='b' access='readwrite'/>"
            "</interface></node>",
            [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Property ‘A.P’ has been removed.'),
                (InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'Property ‘A.P2’ has been added.'),
            ])

    def test_property_type_changed(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<property name='P' type='b' access='readwrite'/>"
            "</interface></node>",
            "<node><interface name='A'>"
            "<property name='P' type='s' access='readwrite'/>"
            "</interface></node>",
            [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Property ‘A.P’ has changed type from ‘b’ to ‘s’.'),
            ])

    def test_property_access_changed_r_to_rw(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<property name='P' type='b' access='read'/>"
            "</interface></node>",
            "<node><interface name='A'>"
            "<property name='P' type='b' access='readwrite'/>"
            "</interface></node>",
            [
                (InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'Property ‘A.P’ has changed access from ‘read’ to '
                 '‘readwrite’, becoming less restrictive.'),
            ])

    def test_property_access_changed_w_to_rw(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<property name='P' type='b' access='write'/>"
            "</interface></node>",
            "<node><interface name='A'>"
            "<property name='P' type='b' access='readwrite'/>"
            "</interface></node>",
            [
                (InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'Property ‘A.P’ has changed access from ‘write’ to '
                 '‘readwrite’, becoming less restrictive.'),
            ])

    def test_property_access_changed_r_to_w(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<property name='P' type='b' access='read'/>"
            "</interface></node>",
            "<node><interface name='A'>"
            "<property name='P' type='b' access='write'/>"
            "</interface></node>",
            [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Property ‘A.P’ has changed access from ‘read’ to ‘write’.'),
            ])

    def test_property_access_changed_rw_to_r(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<property name='P' type='b' access='readwrite'/>"
            "</interface></node>",
            "<node><interface name='A'>"
            "<property name='P' type='b' access='read'/>"
            "</interface></node>",
            [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Property ‘A.P’ has changed access from ‘readwrite’ to '
                 '‘read’.'),
            ])

    def test_property_access_changed_rw_to_w(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<property name='P' type='b' access='readwrite'/>"
            "</interface></node>",
            "<node><interface name='A'>"
            "<property name='P' type='b' access='write'/>"
            "</interface></node>",
            [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Property ‘A.P’ has changed access from ‘readwrite’ to '
                 '‘write’.'),
            ])

    def test_property_emits_changed_signal_changed(self):
        # All the classes of error we expect.
        error1 = (
            InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
            'Node ‘A.P’ started emitting '
            'org.freedesktop.DBus.Properties.PropertiesChanged.'
        )
        error2a = (
            InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
            'Node ‘A.P’ stopped emitting its new value in '
            'org.freedesktop.DBus.Properties.PropertiesChanged.'
        )
        error2b = (
            InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
            'Node ‘A.P’ started emitting its new value in '
            'org.freedesktop.DBus.Properties.PropertiesChanged.'
        )
        error3 = (
            InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
            'Node ‘A.P’ stopped emitting '
            'org.freedesktop.DBus.Properties.PropertiesChanged.'
        )
        error4a = (
            InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
            'Node ‘A.P’ stopped being a constant.'
        )
        error4b = (
            InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
            'Node ‘A.P’ became a constant.'
        )

        # 2D matrix of test vectors. Each row gives the old annotation value;
        # each column the new annotation value. Rows and columns are labelled
        # by the corresponding index in labels. e.g. We expect error2a when
        # changing annotation value from 'true' to 'invalidates'.
        labels = ['true', 'invalidates', 'const', 'false']
        vectors = [
            [None, error2a, error3, error3],
            [error2b, None, error3, error3],
            [error1, error1, None, error4a],
            [error1, error1, error4b, None],
        ]

        for i in range(0, len(vectors)):
            for j in range(0, len(vectors[0])):
                vector = vectors[i][j]
                expected_errors = [vector] if vector is not None else []

                self.assertOutput(
                    "<node><interface name='A'>"
                    "<property name='P' type='b' access='readwrite'>"
                    "<annotation "
                    "name='org.freedesktop.DBus.Property.EmitsChangedSignal' "
                    "value='%s'/>"
                    "</property>"
                    "</interface></node>" % labels[i],
                    "<node><interface name='A'>"
                    "<property name='P' type='b' access='readwrite'>"
                    "<annotation "
                    "name='org.freedesktop.DBus.Property.EmitsChangedSignal' "
                    "value='%s'/>"
                    "</property>"
                    "</interface></node>" % labels[j],
                    expected_errors)

    def test_signal_removed(self):
        self.assertOutput(
            "<node><interface name='A'><signal name='S'/>"
            "</interface></node>",
            "<node><interface name='A'/></node>", [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Signal ‘A.S’ has been removed.'),
            ])

    def test_signal_added(self):
        self.assertOutput(
            "<node><interface name='A'/></node>",
            "<node><interface name='A'><signal name='S'/>"
            "</interface></node>",
            [
                (InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'Signal ‘A.S’ has been added.'),
            ])

    def test_signal_name_changed(self):
        self.assertOutput(
            "<node><interface name='A'><signal name='S'/>"
            "</interface></node>",
            "<node><interface name='A'><signal name='S2'/>"
            "</interface></node>",
            [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Signal ‘A.S’ has been removed.'),
                (InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'Signal ‘A.S2’ has been added.'),
            ])

    def test_signal_arg_removed(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<signal name='S'><arg type='s' direction='in'/></signal>"
            "</interface></node>",
            "<node><interface name='A'><signal name='S'/></interface></node>",
            [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Argument 0 of signal ‘A.S’ has been removed.'),
            ])

    def test_signal_arg_added(self):
        self.assertOutput(
            "<node><interface name='A'><signal name='S'/></interface></node>",
            "<node><interface name='A'>"
            "<signal name='S'><arg type='s' direction='in'/></signal>"
            "</interface></node>",
            [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Argument 0 of signal ‘A.S’ has been added.'),
            ])

    def test_signal_arg_name_changed(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<signal name='S'><arg type='s' name='A' direction='in'/></signal>"
            "</interface></node>",
            "<node><interface name='A'>"
            "<signal name='S'><arg type='s' name='Z' direction='in'/></signal>"
            "</interface></node>",
            [
                (InterfaceComparator.OUTPUT_INFO,
                 'Argument 0 of ‘A.S’ has changed name from ‘A’ to ‘Z’.'),
            ])

    def test_signal_arg_type_changed(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<signal name='S'><arg type='s' direction='in'/></signal>"
            "</interface></node>",
            "<node><interface name='A'>"
            "<signal name='S'><arg type='b' direction='in'/></signal>"
            "</interface></node>",
            [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Argument 0 of ‘A.S’ has changed type from ‘s’ to ‘b’.'),
            ])

    def test_signal_arg_direction_changed(self):
        self.assertOutput(
            "<node><interface name='A'>"
            "<signal name='S'><arg type='s' direction='in'/></signal>"
            "</interface></node>",
            "<node><interface name='A'>"
            "<signal name='S'><arg type='s' direction='out'/></signal>"
            "</interface></node>",
            [
                (InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'Argument 0 of ‘A.S’ has changed direction from ‘in’ to '
                 '‘out’.'),
            ])


if __name__ == '__main__':
    # Run test suite
    unittest.main()
