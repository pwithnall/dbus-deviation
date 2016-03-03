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
            "<node><interface name='I.A'/></node>",
            "<node></node>", [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'interface-removed',
                 'Interface ‘I.A’ has been removed.'),
            ])

    def test_interface_added(self):
        self.assertOutput(
            "<node></node>",
            "<node><interface name='I.A'/></node>", [
                (None, InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'interface-added',
                 'Interface ‘I.A’ has been added.'),
            ])

    def test_interface_deprecated(self):
        self.assertOutput(
            "<node><interface name='I.A'/></node>",
            "<node><interface name='I.A'>"
            "<annotation name='org.freedesktop.DBus.Deprecated' value='true'/>"
            "</interface></node>", [
                (None, InterfaceComparator.OUTPUT_INFO,
                 'deprecated',
                 'Node ‘I.A’ has been deprecated.'),
            ])

    def test_interface_deprecated_explicit(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<annotation name='org.freedesktop.DBus.Deprecated' "
            "value='false'/>"
            "</interface></node>",
            "<node><interface name='I.A'>"
            "<annotation name='org.freedesktop.DBus.Deprecated' value='true'/>"
            "</interface></node>", [
                (None, InterfaceComparator.OUTPUT_INFO,
                 'deprecated',
                 'Node ‘I.A’ has been deprecated.'),
            ])

    def test_interface_undeprecated(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<annotation name='org.freedesktop.DBus.Deprecated' value='true'/>"
            "</interface></node>",
            "<node><interface name='I.A'/></node>", [
                (None, InterfaceComparator.OUTPUT_INFO,
                 'undeprecated',
                 'Node ‘I.A’ has been un-deprecated.'),
            ])

    def test_interface_undeprecated_explicit(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<annotation name='org.freedesktop.DBus.Deprecated' value='true'/>"
            "</interface></node>",
            "<node><interface name='I.A'>"
            "<annotation name='org.freedesktop.DBus.Deprecated' "
            "value='false'/>"
            "</interface></node>", [
                (None, InterfaceComparator.OUTPUT_INFO,
                 'undeprecated',
                 'Node ‘I.A’ has been un-deprecated.'),
            ])

    def test_interface_name_changed(self):
        self.assertOutput(
            "<node><interface name='I.A'/></node>",
            "<node><interface name='I.A2'/></node>", [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'interface-removed',
                 'Interface ‘I.A’ has been removed.'),
                (None, InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'interface-added',
                 'Interface ‘I.A2’ has been added.')
            ])

    def test_method_removed(self):
        self.assertOutput(
            "<node><interface name='I.A'><method name='M'/>"
            "</interface></node>",
            "<node><interface name='I.A'/></node>", [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'method-removed',
                 'Method ‘I.A.M’ has been removed.'),
            ])

    def test_method_added(self):
        self.assertOutput(
            "<node><interface name='I.A'/></node>",
            "<node><interface name='I.A'><method name='M'/>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'method-added',
                 'Method ‘I.A.M’ has been added.'),
            ])

    def test_method_name_changed(self):
        self.assertOutput(
            "<node><interface name='I.A'><method name='M'/>"
            "</interface></node>",
            "<node><interface name='I.A'><method name='M2'/>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'method-removed',
                 'Method ‘I.A.M’ has been removed.'),
                (None, InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'method-added',
                 'Method ‘I.A.M2’ has been added.'),
            ])

    def test_method_arg_removed(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<method name='M'><arg type='s' direction='in'/></method>"
            "</interface></node>",
            "<node><interface name='I.A'><method name='M'/>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'argument-removed',
                 'Argument 0 of method ‘I.A.M’ has been removed.'),
            ])

    def test_method_arg_added(self):
        self.assertOutput(
            "<node><interface name='I.A'><method name='M'/>"
            "</interface></node>",
            "<node><interface name='I.A'>"
            "<method name='M'><arg type='s' direction='in'/></method>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'argument-added',
                 'Argument 0 of method ‘I.A.M’ has been added.'),
            ])

    def test_method_arg_name_changed(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<method name='M'><arg type='s' name='A' direction='in'/>"
            "</method></interface></node>",
            "<node><interface name='I.A'>"
            "<method name='M'><arg type='s' name='Z' direction='in'/>"
            "</method></interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_INFO,
                 'argument-name-changed',
                 'Argument 0 (‘A’) of method ‘I.A.M’ has changed name '
                 'from ‘A’ to ‘Z’.'),
            ])

    def test_method_arg_type_changed(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<method name='M'><arg type='s' direction='in'/></method>"
            "</interface></node>",
            "<node><interface name='I.A'>"
            "<method name='M'><arg type='b' direction='in'/></method>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'argument-type-changed',
                 'Argument 0 of method ‘I.A.M’ has changed type from ‘s’ to '
                 '‘b’.'),
            ])

    def test_method_arg_direction_changed(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<method name='M'><arg type='s' direction='in'/></method>"
            "</interface></node>",
            "<node><interface name='I.A'>"
            "<method name='M'><arg type='s' direction='out'/></method>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'argument-direction-changed-in-out',
                 'Argument 0 of method ‘I.A.M’ has changed direction '
                 'from ‘in’ to ‘out’.'),
            ])

    def test_method_c_symbol_changed(self):
        self.assertOutput(
            "<node><interface name='I.A'><method name='M'>"
            "<annotation name='org.freedesktop.DBus.GLib.CSymbol' value='S1'/>"
            "</method></interface></node>",
            "<node><interface name='I.A'><method name='M'>"
            "<annotation name='org.freedesktop.DBus.GLib.CSymbol' value='S2'/>"
            "</method></interface></node>", [
                (None, InterfaceComparator.OUTPUT_INFO,
                 'c-symbol-changed',
                 'Node ‘I.A.M’ has changed its C symbol from ‘S1’ to ‘S2’.'),
            ])

    def test_method_no_reply_changed_to_false(self):
        self.assertOutput(
            "<node><interface name='I.A'><method name='M'>"
            "<annotation name='org.freedesktop.DBus.Method.NoReply' "
            "value='true'/>"
            "</method></interface></node>",
            "<node><interface name='I.A'><method name='M'>"
            "<annotation name='org.freedesktop.DBus.Method.NoReply' "
            "value='false'/>"
            "</method></interface></node>", [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'reply-added',
                 'Node ‘I.A.M’ has been marked as returning a reply.'),
            ])

    def test_method_no_reply_changed_to_true(self):
        self.assertOutput(
            "<node><interface name='I.A'><method name='M'/>"
            "</interface></node>",
            "<node><interface name='I.A'><method name='M'>"
            "<annotation name='org.freedesktop.DBus.Method.NoReply' "
            "value='true'/>"
            "</method></interface></node>", [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'reply-removed',
                 'Node ‘I.A.M’ has been marked as not returning a reply.'),
            ])

    def test_method_no_reply_changed_to_true_explicit(self):
        self.assertOutput(
            "<node><interface name='I.A'><method name='M'>"
            "<annotation name='org.freedesktop.DBus.Method.NoReply' "
            "value='false'/>"
            "</method></interface></node>",
            "<node><interface name='I.A'><method name='M'>"
            "<annotation name='org.freedesktop.DBus.Method.NoReply' "
            "value='true'/>"
            "</method></interface></node>", [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'reply-removed',
                 'Node ‘I.A.M’ has been marked as not returning a reply.'),
            ])

    def test_property_removed(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<property name='P' type='b' access='readwrite'/>"
            "</interface></node>",
            "<node><interface name='I.A'/></node>", [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'property-removed',
                 'Property ‘I.A.P’ has been removed.'),
            ])

    def test_property_added(self):
        self.assertOutput(
            "<node><interface name='I.A'/></node>",
            "<node><interface name='I.A'>"
            "<property name='P' type='b' access='readwrite'/>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'property-added',
                 'Property ‘I.A.P’ has been added.'),
            ])

    def test_property_name_changed(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<property name='P' type='b' access='readwrite'/>"
            "</interface></node>",
            "<node><interface name='I.A'>"
            "<property name='P2' type='b' access='readwrite'/>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'property-removed',
                 'Property ‘I.A.P’ has been removed.'),
                (None, InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'property-added',
                 'Property ‘I.A.P2’ has been added.'),
            ])

    def test_property_type_changed(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<property name='P' type='b' access='readwrite'/>"
            "</interface></node>",
            "<node><interface name='I.A'>"
            "<property name='P' type='s' access='readwrite'/>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'property-type-changed',
                 'Property ‘I.A.P’ has changed type from ‘b’ to ‘s’.'),
            ])

    def test_property_access_changed_r_to_rw(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<property name='P' type='b' access='read'/>"
            "</interface></node>",
            "<node><interface name='I.A'>"
            "<property name='P' type='b' access='readwrite'/>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'property-access-changed-read-readwrite',
                 'Property ‘I.A.P’ has changed access from ‘read’ to '
                 '‘readwrite’, becoming less restrictive.'),
            ])

    def test_property_access_changed_w_to_rw(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<property name='P' type='b' access='write'/>"
            "</interface></node>",
            "<node><interface name='I.A'>"
            "<property name='P' type='b' access='readwrite'/>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'property-access-changed-write-readwrite',
                 'Property ‘I.A.P’ has changed access from ‘write’ to '
                 '‘readwrite’, becoming less restrictive.'),
            ])

    def test_property_access_changed_r_to_w(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<property name='P' type='b' access='read'/>"
            "</interface></node>",
            "<node><interface name='I.A'>"
            "<property name='P' type='b' access='write'/>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'property-access-changed-read-write',
                 'Property ‘I.A.P’ has changed access '
                 'from ‘read’ to ‘write’.'),
            ])

    def test_property_access_changed_rw_to_r(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<property name='P' type='b' access='readwrite'/>"
            "</interface></node>",
            "<node><interface name='I.A'>"
            "<property name='P' type='b' access='read'/>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'property-access-changed-readwrite-read',
                 'Property ‘I.A.P’ has changed access from ‘readwrite’ to '
                 '‘read’.'),
            ])

    def test_property_access_changed_rw_to_w(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<property name='P' type='b' access='readwrite'/>"
            "</interface></node>",
            "<node><interface name='I.A'>"
            "<property name='P' type='b' access='write'/>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'property-access-changed-readwrite-write',
                 'Property ‘I.A.P’ has changed access from ‘readwrite’ to '
                 '‘write’.'),
            ])

    def test_property_emits_changed_signal_changed(self):
        # All the classes of error we expect.
        error1 = (
            InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
            'Node ‘I.A.P’ started emitting '
            'org.freedesktop.DBus.Properties.PropertiesChanged.'
        )
        error2a = (
            InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
            'Node ‘I.A.P’ stopped emitting its new value in '
            'org.freedesktop.DBus.Properties.PropertiesChanged.'
        )
        error2b = (
            InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
            'Node ‘I.A.P’ started emitting its new value in '
            'org.freedesktop.DBus.Properties.PropertiesChanged.'
        )
        error3 = (
            InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
            'Node ‘I.A.P’ stopped emitting '
            'org.freedesktop.DBus.Properties.PropertiesChanged.'
        )
        error4a = (
            InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
            'Node ‘I.A.P’ stopped being a constant.'
        )
        error4b = (
            InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
            'Node ‘I.A.P’ became a constant.'
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
                if vector is not None:
                    vector = (
                        None,
                        vector[0],
                        'ecs-changed-%s-%s' % (labels[i], labels[j]),
                        vector[1],
                    )
                expected_errors = [vector] if vector is not None else []

                self.assertOutput(
                    "<node><interface name='I.A'>"
                    "<property name='P' type='b' access='readwrite'>"
                    "<annotation "
                    "name='org.freedesktop.DBus.Property.EmitsChangedSignal' "
                    "value='%s'/>"
                    "</property>"
                    "</interface></node>" % labels[i],
                    "<node><interface name='I.A'>"
                    "<property name='P' type='b' access='readwrite'>"
                    "<annotation "
                    "name='org.freedesktop.DBus.Property.EmitsChangedSignal' "
                    "value='%s'/>"
                    "</property>"
                    "</interface></node>" % labels[j],
                    expected_errors)

    def test_signal_removed(self):
        self.assertOutput(
            "<node><interface name='I.A'><signal name='S'/>"
            "</interface></node>",
            "<node><interface name='I.A'/></node>", [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'signal-removed',
                 'Signal ‘I.A.S’ has been removed.'),
            ])

    def test_signal_added(self):
        self.assertOutput(
            "<node><interface name='I.A'/></node>",
            "<node><interface name='I.A'><signal name='S'/>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'signal-added',
                 'Signal ‘I.A.S’ has been added.'),
            ])

    def test_signal_name_changed(self):
        self.assertOutput(
            "<node><interface name='I.A'><signal name='S'/>"
            "</interface></node>",
            "<node><interface name='I.A'><signal name='S2'/>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'signal-removed',
                 'Signal ‘I.A.S’ has been removed.'),
                (None, InterfaceComparator.OUTPUT_FORWARDS_INCOMPATIBLE,
                 'signal-added',
                 'Signal ‘I.A.S2’ has been added.'),
            ])

    def test_signal_arg_removed(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<signal name='S'><arg type='s' direction='in'/></signal>"
            "</interface></node>",
            "<node><interface name='I.A'><signal name='S'/>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'argument-removed',
                 'Argument 0 of signal ‘I.A.S’ has been removed.'),
            ])

    def test_signal_arg_added(self):
        self.assertOutput(
            "<node><interface name='I.A'><signal name='S'/>"
            "</interface></node>",
            "<node><interface name='I.A'>"
            "<signal name='S'><arg type='s' direction='in'/></signal>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'argument-added',
                 'Argument 0 of signal ‘I.A.S’ has been added.'),
            ])

    def test_signal_arg_name_changed(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<signal name='S'><arg type='s' name='A' direction='in'/></signal>"
            "</interface></node>",
            "<node><interface name='I.A'>"
            "<signal name='S'><arg type='s' name='Z' direction='in'/></signal>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_INFO,
                 'argument-name-changed',
                 'Argument 0 (‘A’) of signal ‘I.A.S’ has changed name '
                 'from ‘A’ to ‘Z’.'),
            ])

    def test_signal_arg_type_changed(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<signal name='S'><arg type='s' direction='in'/></signal>"
            "</interface></node>",
            "<node><interface name='I.A'>"
            "<signal name='S'><arg type='b' direction='in'/></signal>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'argument-type-changed',
                 'Argument 0 of signal ‘I.A.S’ has changed type from ‘s’ to '
                 '‘b’.'),
            ])

    def test_signal_arg_direction_changed(self):
        self.assertOutput(
            "<node><interface name='I.A'>"
            "<signal name='S'><arg type='s' direction='in'/></signal>"
            "</interface></node>",
            "<node><interface name='I.A'>"
            "<signal name='S'><arg type='s' direction='out'/></signal>"
            "</interface></node>",
            [
                (None, InterfaceComparator.OUTPUT_BACKWARDS_INCOMPATIBLE,
                 'argument-direction-changed-in-out',
                 'Argument 0 of signal ‘I.A.S’ has changed direction '
                 'from ‘in’ to ‘out’.'),
            ])


if __name__ == '__main__':
    # Run test suite
    unittest.main()
