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
Unit tests for dbusapi.interfaceparser
"""


# pylint: disable=missing-docstring


from dbusapi.interfaceparser import InterfaceParser
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


def _test_parser_with_nodes(xml):
    """Build an InterfaceParser for the XML snippet and parse it."""
    tmpfile = _create_temp_xml_file(xml)
    parser = InterfaceParser(tmpfile)
    root_node = parser.parse_with_nodes()
    os.unlink(tmpfile)
    return parser, root_node, tmpfile


def _test_parser(xml):
    """Build an InterfaceParser for the XML snippet and parse it."""
    parser, root_node, tmpfile = _test_parser_with_nodes(xml)
    interfaces = root_node.interfaces if root_node else None
    return parser, interfaces, tmpfile


# pylint: disable=too-many-public-methods
class TestParserErrors(unittest.TestCase):
    """Test error handling in the InterfaceParser."""

    # pylint: disable=invalid-name
    def assertOutputWithNodes(self, xml, partial_output):  # noqa
        (parser, root_node, filename) = _test_parser_with_nodes(xml)
        self.assertEqual(root_node, None)
        actual_output = \
            [(filename, 'parser', i[0], i[1]) for i in partial_output]
        self.assertEqual(parser.get_output(), actual_output)

    # pylint: disable=invalid-name
    def assertOutput(self, xml, partial_output):  # noqa
        (parser, interfaces, filename) = _test_parser(xml)
        self.assertEqual(interfaces, None)
        actual_output = \
            [(filename, 'parser', i[0], i[1]) for i in partial_output]
        self.assertEqual(parser.get_output(), actual_output)

    def test_unknown_root_node(self):
        self.assertOutput(
            "<notnode><irrelevant/></notnode>", [
                ('unknown-node', 'Unknown root node ‘notnode’.'),
            ])

    def test_nonabsolute_node_name(self):
        self.assertOutputWithNodes(
            "<node name='rel/N'></node>", [
                ('node-name',
                 'Root node name is not an absolute object path ‘rel/N’.'),
            ])

    def test_invalid_node_name(self):
        self.assertOutputWithNodes(
            "<node name='//'></node>", [
                ('node-name',
                 'Root node name is not an absolute object path ‘//’.'),
            ])

    def test_missing_node_name(self):
        self.assertOutputWithNodes(
            "<node><node /></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘name’ in non-root node.'),
            ])

    def test_nonrelative_node_name(self):
        self.assertOutputWithNodes(
            "<node><node name='/abs/N'/></node>", [
                ('node-name',
                 'Non-root node name is not a relative object path ‘/abs/N’.'),
            ])

    def test_duplicate_node(self):
        self.assertOutputWithNodes(
            "<node><node name='N'/><node name='N'/></node>", [
                ('duplicate-node',
                 'Duplicate node definition ‘N’.'),
            ])

    def test_invalid_interface_name(self):
        self.assertOutput(
            "<node><interface name='0'/></node>", [
                ('interface-name',
                 'Invalid interface name ‘0’.'),
            ])

    def test_duplicate_interface(self):
        self.assertOutput(
            "<node><interface name='I.I'/><interface name='I.I'/></node>", [
                ('duplicate-interface',
                 'Duplicate interface definition ‘I.I’.'),
            ])

    def test_unknown_interface_node(self):
        self.assertOutput(
            "<node><badnode/></node>", [
                ('unknown-node', 'Unknown node ‘badnode’ in root.'),
            ])

    def test_interface_missing_name(self):
        self.assertOutput(
            "<node><interface/></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘name’ in interface.'),
            ])

    def test_invalid_method(self):
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<method name='0M'/>"
            "</interface></node>", [
                ('method-name',
                 'Invalid method name ‘0M’.'),
            ])

    def test_duplicate_method(self):
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<method name='M'/><method name='M'/>"
            "</interface></node>", [
                ('duplicate-method',
                 'Duplicate method definition ‘I.I.M’.'),
            ])

    def test_invalid_signal(self):
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<signal name='*S'/>"
            "</interface></node>", [
                ('signal-name',
                 'Invalid signal name ‘*S’.'),
            ])

    def test_duplicate_signal(self):
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<signal name='S'/><signal name='S'/>"
            "</interface></node>", [
                ('duplicate-signal',
                 'Duplicate signal definition ‘I.I.S’.'),
            ])

    def test_invalid_signal_signature(self):
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<signal name='S'><arg name='N' type='?'/></signal>"
            "</interface></node>", [
                ('argument-type',
                 'Error when parsing type ‘?’ for argument ‘N’: '
                 'Reserved type ‘?’ must not be used in signatures on D-Bus.'),
            ])

    def test_duplicate_property(self):
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<property name='P' type='s' access='readwrite'/>"
            "<property name='P' type='s' access='readwrite'/>"
            "</interface></node>", [
                ('duplicate-property',
                 'Duplicate property definition ‘I.I.P’.'),
            ])

    def test_invalid_property_signature(self):
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<property name='P' type='a?' access='readwrite'/>"
            "</interface></node>", [
                ('property-type',
                 'Error when parsing type ‘a?’ for property ‘P’: '
                 'Reserved type ‘?’ must not be used in signatures on D-Bus.'),
            ])

    def test_unknown_sub_interface_node(self):
        self.assertOutput(
            "<node><interface name='I.I'><badnode/></interface></node>", [
                ('unknown-node', 'Unknown node ‘badnode’ in interface ‘I.I’.'),
            ])

    def test_method_missing_name(self):
        self.assertOutput(
            "<node><interface name='I.I'><method/></interface></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘name’ in method.'),
            ])

    def test_unknown_method_node(self):
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<method name='M'><badnode/></method>"
            "</interface></node>", [
                ('unknown-node', 'Unknown node ‘badnode’ in method ‘I.I.M’.'),
            ])

    def test_signal_missing_name(self):
        self.assertOutput(
            "<node><interface name='I.I'><signal/></interface></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘name’ in signal.'),
            ])

    def test_unknown_signal_node(self):
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<signal name='S'><badnode/></signal>"
            "</interface></node>", [
                ('unknown-node', 'Unknown node ‘badnode’ in signal ‘I.I.S’.'),
            ])

    def test_property_missing_name(self):
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<property type='s' access='readwrite'/>"
            "</interface></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘name’ in property.'),
            ])

    def test_property_missing_type(self):
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<property name='P' access='readwrite'/>"
            "</interface></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘type’ in property.'),
            ])

    def test_property_missing_access(self):
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<property name='P' type='s'/>"
            "</interface></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘access’ in property.'),
            ])

    def test_unknown_property_node(self):
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<property name='P' type='s' access='readwrite'>"
            "<badnode/>"
            "</property>"
            "</interface></node>", [
                ('unknown-node',
                 'Unknown node ‘badnode’ in property ‘I.I.P’.'),
            ])

    def test_unknown_arg_node(self):
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<method name='M'><arg type='s'><badnode/></arg></method>"
            "</interface></node>", [
                ('unknown-node',
                 'Unknown node ‘badnode’ in argument ‘0 of method ‘I.I.M’’.'),
            ])

    def test_arg_missing_type(self):
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<method name='M'><arg/></method>"
            "</interface></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘type’ in arg.'),
            ])

    def test_annotation_missing_name(self):
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<annotation value='V'/>"
            "</interface></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘name’ in annotation.'),
            ])

    def test_unknown_annotation_node(self):
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<annotation name='N' value='V'><badnode/></annotation>"
            "</interface></node>", [
                ('unknown-node',
                 'Unknown node ‘badnode’ in annotation ‘N of ‘I.I’’.'),
            ])


# pylint: disable=too-many-public-methods
class TestParserNormal(unittest.TestCase):
    """Test normal parsing of unusual input in the InterfaceParser."""

    # pylint: disable=invalid-name
    def assertParse(self, xml):  # noqa
        (parser, interfaces, _) = _test_parser(xml)
        self.assertEqual(parser.get_output(), [])
        return interfaces

    def test_tp_spec_root(self):
        """Test that specifications wrapped in tp:spec are parsed."""
        self.assertParse(
            "<tp:spec xmlns:tp='"
            "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
            "'><node><interface name='I.I'/></node></tp:spec>")

    def test_ignored_namespaced_tags_interface(self):
        self.assertParse(
            "<node><ignored:spec xmlns:ignored='http://ignored.com'>"
            "<interface name='I.I'/></ignored:spec></node>")

    def test_ignored_namespaced_tags(self):
        self.assertParse(
            "<node>"
            "<interface name='I.I'>"
            "<ignored:spec xmlns:ignored='http://ignored.com'>"
            "</ignored:spec>"
            "</interface></node>")

    def test_doc_root(self):
        """Test that doc tags are ignored in the root."""
        self.assertParse(
            "<node xmlns:tp='"
            "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
            "' xmlns:doc='"
            "http://www.freedesktop.org/dbus/1.0/doc.dtd"
            "'>"
            "<tp:docstring>Ignore me.</tp:docstring>"
            "<doc:doc>Ignore me.</doc:doc>"
            "</node>")

    def test_doc_interface(self):
        """Test that doc tags are ignored in interfaces."""
        self.assertParse(
            "<node xmlns:tp='"
            "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
            "' xmlns:doc='"
            "http://www.freedesktop.org/dbus/1.0/doc.dtd"
            "'><interface name='I.I'>"
            "<tp:docstring>Ignore me.</tp:docstring>"
            "<doc:doc>Ignore me.</doc:doc>"
            "</interface></node>")

    def test_doc_method(self):
        """Test that doc tags are ignored in methods."""
        self.assertParse(
            "<node xmlns:tp='"
            "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
            "' xmlns:doc='"
            "http://www.freedesktop.org/dbus/1.0/doc.dtd"
            "'><interface name='I.I'><method name='M'>"
            "<tp:docstring>Ignore me.</tp:docstring>"
            "<doc:doc>Ignore me.</doc:doc>"
            "</method></interface></node>")

    def test_doc_signal(self):
        """Test that doc tags are ignored in signals."""
        self.assertParse(
            "<node xmlns:tp='"
            "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
            "' xmlns:doc='"
            "http://www.freedesktop.org/dbus/1.0/doc.dtd"
            "'><interface name='I.I'><signal name='S'>"
            "<tp:docstring>Ignore me.</tp:docstring>"
            "<doc:doc>Ignore me.</doc:doc>"
            "</signal></interface></node>")

    def test_doc_property(self):
        """Test that doc tags are ignored in properties."""
        self.assertParse(
            "<node xmlns:tp='"
            "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
            "' xmlns:doc='"
            "http://www.freedesktop.org/dbus/1.0/doc.dtd'>"
            "<interface name='I.I'><property name='P' type='s' access='read'>"
            "<tp:docstring>Ignore me.</tp:docstring>"
            "<doc:doc>Ignore me.</doc:doc>"
            "</property></interface></node>")

    def test_doc_arg(self):
        """Test that doc tags are ignored in args."""
        self.assertParse(
            "<node xmlns:tp='"
            "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
            "' xmlns:doc='"
            "http://www.freedesktop.org/dbus/1.0/doc.dtd"
            "'><interface name='I.I'><method name='M'><arg type='s'>"
            "<tp:docstring>Ignore me.</tp:docstring>"
            "<doc:doc>Ignore me.</doc:doc>"
            "</arg></method></interface></node>")

    def test_doc_annotation(self):
        """Test that doc tags are ignored in annotations."""
        self.assertParse(
            "<node xmlns:tp='"
            "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
            "' xmlns:doc='"
            "http://www.freedesktop.org/dbus/1.0/doc.dtd"
            "'><interface name='I.I'><annotation name='A' value='V'>"
            "<tp:docstring>Ignore me.</tp:docstring>"
            "<doc:doc>Ignore me.</doc:doc>"
            "</annotation></interface></node>")

    def test_doc_comments(self):
        """Test that xml comments are *not* ignored"""
        xml = ("<node xmlns:tp='"
               "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
               "' xmlns:doc='"
               "http://www.freedesktop.org/dbus/1.0/doc.dtd'>"
               "<!--"
               "Please consider me"
               "-->"
               "<interface name='I.I'>"
               "<!--"
               "Notice me too"
               "-->"
               "<method name='foo'>"
               "<!--"
               "And me!"
               "-->"
               "<arg name='bar' type='s'/>"
               "</method>"
               "</interface></node>")

        (parser, interfaces, _) = _test_parser(xml)
        interface = interfaces.get('I.I')
        self.assertIsNotNone(interface)
        self.assertEquals(interface.comment, "Please consider me")
        meth = interface.methods.get('foo')
        self.assertIsNotNone(meth)
        self.assertEquals(meth.comment, "Notice me too")
        self.assertEquals(len(meth.arguments), 1)
        arg = meth.arguments[0]
        self.assertEquals(arg.comment, "And me!")

    def test_line_numbers(self):
        """Test that line numbers are correctly computed"""
        xml = ("<node xmlns:tp='"
               "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
               "' xmlns:doc='"
               "http://www.freedesktop.org/dbus/1.0/doc.dtd'>\n"
               "<!--\n"
               "Please consider me\n"
               "-->\n"
               "<interface name='I.I'>\n"
               "<!--\n"
               "Notice me too\n"
               "-->\n"
               "<method name='foo'>\n"
               "<!--\n"
               "And me!\n"
               "-->\n"
               "<arg name='bar' type='s'/>\n"
               "<arg name='no-comment' type='s'/>\n"
               "</method>\n"
               "</interface></node>\n")

        (parser, interfaces, _) = _test_parser(xml)
        interface = interfaces.get('I.I')
        self.assertIsNotNone(interface)
        self.assertEqual(interface.line_number, 5)
        self.assertEqual(interface.comment_line_number, 2)
        meth = interface.methods.get('foo')
        self.assertIsNotNone(meth)
        self.assertEqual(meth.line_number, 9)
        self.assertEqual(meth.comment_line_number, 6)
        self.assertEquals(len(meth.arguments), 2)
        arg = meth.arguments[0]
        self.assertEqual(arg.line_number, 13)
        self.assertEqual(arg.comment_line_number, 10)
        arg = meth.arguments[1]
        self.assertEqual(arg.line_number, 14)
        self.assertEqual(arg.comment_line_number, -1)

    def test_doc_annotations(self):
        xml = ("<node xmlns:tp='"
               "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
               "' xmlns:doc='"
               "http://www.freedesktop.org/dbus/1.0/doc.dtd'>"
               "<interface name='I.I'>"
               "<annotation name='org.gtk.GDBus.DocString' value='bla'/>"
               "</interface></node>")
        (parser, interfaces, _) = _test_parser(xml)
        interface = interfaces.get('I.I')
        self.assertIsNotNone(interface)
        self.assertEquals(interface.comment, "bla")

    def test_multiline_comments(self):
        xml = ("<node xmlns:tp='"
               "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
               "' xmlns:doc='"
               "http://www.freedesktop.org/dbus/1.0/doc.dtd'>"
               "<!--"
               "    Please consider that\n"
               "    multiline comment"
               "-->"
               "<interface name='I.I'>"
               "</interface></node>")

        (parser, interfaces, _) = _test_parser(xml)
        interface = interfaces.get('I.I')
        self.assertIsNotNone(interface)
        self.assertEquals(interface.comment,
                          "    Please consider that\n"
                          "    multiline comment")

    def test_ignored_comments(self):
        xml = ("<node xmlns:tp='"
               "http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0"
               "' xmlns:doc='"
               "http://www.freedesktop.org/dbus/1.0/doc.dtd'>"
               "<!--"
               "Please ignore that comment"
               "-->"
               "<tp:copyright>"
               "</tp:copyright>"
               "<interface name='I.I'>"
               "</interface></node>")

        (parser, interfaces, _) = _test_parser(xml)
        interface = interfaces.get('I.I')
        self.assertIsNotNone(interface)
        self.assertIsNone(interface.comment)

    def test_root_node(self):
        self.assertParse("""<node name="/" />""")

    def test_dbus_spec_example(self):
        """
        Test parsing the example from the D-Bus Specification:

            http://dbus.freedesktop.org/doc/dbus-specification.html#introspection-format
        """
        self.assertParse("""
<!DOCTYPE node PUBLIC "-//freedesktop//DTD D-BUS Object Introspection 1.0//EN"
 "http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd">
<node name="/com/example/sample_object">
  <interface name="com.example.SampleInterface">
    <method name="Frobate">
      <arg name="foo" type="i" direction="in"/>
      <arg name="bar" type="s" direction="out"/>
      <arg name="baz" type="a{us}" direction="out"/>
      <annotation name="org.freedesktop.DBus.Deprecated" value="true"/>
    </method>
    <method name="Bazify">
      <arg name="bar" type="(iiu)" direction="in"/>
      <arg name="bar" type="v" direction="out"/>
    </method>
    <method name="Mogrify">
      <arg name="bar" type="(iiav)" direction="in"/>
    </method>
    <signal name="Changed">
      <arg name="new_value" type="b"/>
    </signal>
    <property name="Bar" type="y" access="readwrite"/>
  </interface>
  <node name="child_of_sample_object"/>
  <node name="another_child_of_sample_object"/>
</node>""")


class TestParserOutputCodes(unittest.TestCase):
    """Test the output codes from InterfaceParser."""

    def test_unique(self):
        codes = InterfaceParser.get_output_codes()
        self.assertEqual(len(codes), len(set(codes)))

    def test_non_empty(self):
        codes = InterfaceParser.get_output_codes()
        self.assertNotEqual(codes, [])


# pylint: disable=too-many-public-methods
class TestParserRecovery(unittest.TestCase):
    """
    Test recovery from parser errors in InterfaceParser to detect subsequent
    errors.
    """

    # pylint: disable=invalid-name
    def assertOutput(self, xml, partial_output):  # noqa
        (parser, interfaces, filename) = _test_parser(xml)
        self.assertEqual(interfaces, None)
        actual_output = \
            [(filename, 'parser', i[0], i[1]) for i in partial_output]
        self.assertEqual(parser.get_output(), actual_output)
        return interfaces

    def test_annotation_interface(self):
        """Test recovery from invalid annotations in an interface."""
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<annotation/><method/>"
            "</interface></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘name’ in annotation.'),
                ('missing-attribute',
                 'Missing required attribute ‘name’ in method.'),
            ])

    def test_annotation_method(self):
        """Test recovery from invalid annotations in a method."""
        self.assertOutput(
            "<node><interface name='I.I'><method name='M'>"
            "<annotation/><arg/>"
            "</method></interface></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘name’ in annotation.'),
                ('missing-attribute',
                 'Missing required attribute ‘type’ in arg.'),
            ])

    def test_annotation_signal(self):
        """Test recovery from invalid annotations in a signal."""
        self.assertOutput(
            "<node><interface name='I.I'><signal name='S'>"
            "<annotation/><arg/>"
            "</signal></interface></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘name’ in annotation.'),
                ('missing-attribute',
                 'Missing required attribute ‘type’ in arg.'),
            ])

    def test_annotation_property(self):
        """Test recovery from invalid annotations in a property."""
        self.assertOutput(
            "<node><interface name='I.I'>"
            "<property name='P' type='s' access='read'>"
            "<annotation/><badnode/>"
            "</property>"
            "</interface></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘name’ in annotation.'),
                ('unknown-node',
                 'Unknown node ‘badnode’ in property ‘I.I.P’.'),
            ])

    def test_annotation_arg(self):
        """Test recovery from invalid annotations in an arg."""
        self.assertOutput(
            "<node><interface name='I.I'><method name='M'><arg type='s'>"
            "<annotation/><badnode/>"
            "</arg></method></interface></node>", [
                ('missing-attribute',
                 'Missing required attribute ‘name’ in annotation.'),
                ('unknown-node',
                 'Unknown node ‘badnode’ in argument ‘0 of method ‘I.I.M’’.'),
            ])


if __name__ == '__main__':
    # Run test suite
    unittest.main()
