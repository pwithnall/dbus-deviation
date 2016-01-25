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
TODO
"""

import os

# PyPy support
# pylint: disable=interface-not-implemented
try:
    from xml.etree import cElementTree as ElementTree
except ImportError:
    from xml.etree import ElementTree

from dbusapi import ast
from dbusapi.typeparser import TypeParser


def _ignore_node(node):
    """
    Decide whether to ignore the given node when parsing.

    We definitely want to ignore:
     * {http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0}docstring
     * {http://www.freedesktop.org/dbus/1.0/doc.dtd}doc
    """
    return node.tag[0] == '{'  # in a namespace


# pylint: disable=interface-not-implemented
class InterfaceParser(object):

    """
    Parse a D-Bus introspection XML file.

    This validates the file, but not exceedingly strictly. It is a pragmatic
    parser, designed for use by the InterfaceComparator rather than more
    general code. It ignores certain common extensions found in introspection
    XML files, such as documentation elements, but will fail on other
    unrecognised elements.
    """

    TP_DTD = 'http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0'

    def __init__(self, filename):
        """
        Construct a new InterfaceParser.

        Args:
            filename: path to the XML introspection file to parse
        """
        self._filename = filename
        self._output = []

    @staticmethod
    def get_output_codes():
        """Return a list of all possible output codes."""
        # FIXME: Hard-coded for the moment.
        return [
            'unknown-node',
            'node-naming'
            'duplicate-node',
            'duplicate-interface',
            'missing-attribute',
            'duplicate-method',
            'duplicate-signal',
            'duplicate-property',
            'invalid-signature',
        ]

    def _issue_output(self, code, message):
        """Append a message to the parser output."""
        self._output.append((self._filename, 'parser', code, message))

    def get_output(self):
        """Return a list of all logged parser messages."""
        return self._output

    def parse(self):
        """
        Parse the introspection XML file and build an AST.

        Returns:
            A non-empty dict of interfaces in the file, mapping each interface
            name to an ast.Interface instance.

            If parsing fails, None is returned.
        """
        self._output = []
        tree = ElementTree.parse(os.path.abspath(self._filename))
        out = self._parse_root(tree.getroot())

        # Squash output on error.
        if self._output:
            return None

        return out

    def _parse_root(self, root):
        """Parse the root node in the XML tree; return a dict of interfaces."""
        # Handle specifications wrapped in tp:spec.
        if root.tag == '{%s}spec' % self.TP_DTD:
            for node in root.getchildren():
                if node.tag == 'node':
                    root = node
                    break

        # Continue parsing as per the D-Bus introspection format

        if root.tag != 'node':
            self._issue_output('unknown-node',
                               'Unknown root node ‘%s’.' % root.tag)
            return None

        root_node = self._parse_node(root)

        if root_node.name and not root_node.name[0] == '/':
            self._issue_output('node-naming',
                               'Root node name is not an absolute object path ‘%s’.' % root_node.name)
            return None

        return root_node

    def _parse_node(self, node_node):
        """Parse a <node> element; return an ast.Node or None."""
        assert node_node.tag == 'node'

        if 'name' in node_node.attrib:
            name = node_node.attrib['name']
        else:
            name = None
        nodes = {}
        interfaces = {}

        for node in node_node.getchildren():
            if node.tag == 'interface':
                interface = self._parse_interface(node)
                if interface is None:
                    continue

                if interface.name in interfaces:
                    self._issue_output('duplicate-interface',
                                       'Duplicate interface definition ‘%s’.' %
                                       interface.format_name())
                    continue

                interfaces[interface.name] = interface
            elif node.tag == 'node':
                sub_node = self._parse_node(node)
                if sub_node is None:
                    continue

                if not sub_node.name:
                    self._issue_output('missing-attribute',
                                       'Missing required attribute ‘name’ in non-root node.')
                    continue

                if sub_node.name[0] == '/':
                    self._issue_output('node-naming',
                                       'Non-root node name is not a relative object path ‘%s’.' % sub_node.name)
                    continue

                if sub_node.name in nodes:
                    self._issue_output('duplicate-node',
                                       'Duplicate node definition ‘%s’.' %
                                       sub_node.format_name())
                    continue

                nodes[sub_node.name] = sub_node
            elif _ignore_node(node):
                pass
            else:
                self._issue_output('unknown-node',
                                   'Unknown node ‘%s’ in root.' %
                                   node.tag)

        return ast.Node(name, interfaces, nodes)

    # pylint: disable=too-many-branches
    def _parse_interface(self, interface_node):  # noqa
        """Parse an <interface> element; return an ast.Interface or None."""
        assert interface_node.tag == 'interface'

        if 'name' not in interface_node.attrib:
            self._issue_output('missing-attribute',
                               'Missing required attribute ‘%s’ in '
                               'interface.' % 'name')
            return None

        name = interface_node.attrib['name']
        methods = {}
        signals = {}
        properties = {}
        annotations = {}

        for node in interface_node.getchildren():
            if node.tag == 'method':
                method = self._parse_method(node, name)
                if method is None:
                    continue

                if method.name in methods:
                    self._issue_output('duplicate-method',
                                       'Duplicate method definition ‘%s.%s’.' %
                                       (name, method.format_name()))
                    continue

                methods[method.name] = method
            elif node.tag == 'signal':
                signal = self._parse_signal(node, name)
                if signal is None:
                    continue

                if signal.name in signals:
                    self._issue_output('duplicate-signal',
                                       'Duplicate signal definition ‘%s.%s’.' %
                                       (name, signal.format_name()))
                    continue

                signals[signal.name] = signal
            elif node.tag == 'property':
                prop = self._parse_property(node, name)
                if prop is None:
                    continue

                if prop.name in properties:
                    self._issue_output('duplicate-property',
                                       'Duplicate property definition '
                                       '‘%s.%s’.' %
                                       (name, prop.format_name()))
                    continue

                properties[prop.name] = prop
            elif node.tag == 'annotation':
                annotation = self._parse_annotation(node, name)
                if annotation is None:
                    continue

                annotations[annotation.name] = annotation
            elif _ignore_node(node):
                pass
            else:
                self._issue_output('unknown-node',
                                   'Unknown node ‘%s’ in interface '
                                   '‘%s’.' % (node.tag, name))

        return ast.Interface(name, methods, properties, signals,
                             annotations)

    def _parse_method(self, method_node, interface_name=None):
        """Parse a <method> element; return an ast.Method or None."""
        assert method_node.tag == 'method'

        if 'name' not in method_node.attrib:
            self._issue_output('missing-attribute',
                               'Missing required attribute ‘%s’ in method.' %
                               'name')
            return None

        name = method_node.attrib['name']
        args = []
        annotations = {}

        pretty_method_name = interface_name + '.' + name

        for node in method_node.getchildren():
            if node.tag == 'arg':
                arg = self._parse_arg(node, pretty_method_name)
                if arg is None:
                    continue

                args.append(arg)
            elif node.tag == 'annotation':
                annotation = self._parse_annotation(node, pretty_method_name)
                if annotation is None:
                    continue

                annotations[annotation.name] = annotation
            elif _ignore_node(node):
                pass
            else:
                self._issue_output('unknown-node',
                                   'Unknown node ‘%s’ in method ‘%s’.' %
                                   (node.tag, pretty_method_name))

        return ast.Method(name, args, annotations)

    def _parse_signal(self, signal_node, interface_name=None):
        """Parse a <signal> element; return an ast.Signal or None."""
        assert signal_node.tag == 'signal'

        if 'name' not in signal_node.attrib:
            self._issue_output('missing-attribute',
                               'Missing required attribute ‘%s’ in signal.' %
                               'name')
            return None

        name = signal_node.attrib['name']
        args = []
        annotations = {}

        pretty_signal_name = interface_name + '.' + name

        for node in signal_node.getchildren():
            if node.tag == 'arg':
                arg = self._parse_arg(node, pretty_signal_name)
                if arg is None:
                    continue

                args.append(arg)
            elif node.tag == 'annotation':
                annotation = self._parse_annotation(node, pretty_signal_name)
                if annotation is None:
                    continue

                annotations[annotation.name] = annotation
            elif _ignore_node(node):
                pass
            else:
                self._issue_output('unknown-node',
                                   'Unknown node ‘%s’ in signal ‘%s’.' %
                                   (node.tag, pretty_signal_name))

        return ast.Signal(name, args, annotations)

    def _parse_property(self, property_node, interface_name=None):
        """Parse a <property> element; return an ast.Property or None."""
        assert property_node.tag == 'property'

        if 'name' not in property_node.attrib:
            self._issue_output('missing-attribute',
                               'Missing required attribute ‘%s’ in property.' %
                               'name')
            return None
        elif 'type' not in property_node.attrib:
            self._issue_output('missing-attribute',
                               'Missing required attribute ‘%s’ in property.' %
                               'type')
            return None
        elif 'access' not in property_node.attrib:
            self._issue_output('missing-attribute',
                               'Missing required attribute ‘%s’ in property.' %
                               'access')
            return None

        name = property_node.attrib['name']
        prop_type = property_node.attrib['type']
        access = property_node.attrib['access']
        annotations = {}

        pretty_prop_name = interface_name + '.' + name

        for node in property_node.getchildren():
            if node.tag == 'annotation':
                annotation = self._parse_annotation(node, pretty_prop_name)
                if annotation is None:
                    continue

                annotations[annotation.name] = annotation
            elif _ignore_node(node):
                pass
            else:
                self._issue_output('unknown-node',
                                   'Unknown node ‘%s’ in property ‘%s’.' %
                                   (node.tag, pretty_prop_name))

        type_parser = TypeParser(prop_type)
        type = type_parser.parse()
        if not type:
            self._issue_output('invalid-signature',
                               type_parser.get_output()[1])
            return None

        return ast.Property(name, type, access, annotations)

    def _parse_arg(self, arg_node, parent_name=None):
        """Parse an <arg> element; return an ast.Argument or None."""
        assert arg_node.tag == 'arg'

        if 'type' not in arg_node.attrib:
            self._issue_output('missing-attribute',
                               'Missing required attribute ‘%s’ in arg.' %
                               'type')
            return None

        name = arg_node.attrib.get('name', None)
        direction = arg_node.attrib.get('direction',
                                        ast.Argument.DIRECTION_IN)
        arg_type = arg_node.attrib['type']
        annotations = {}

        pretty_arg_name = name if name is not None else 'unnamed'

        for node in arg_node.getchildren():
            if node.tag == 'annotation':
                annotation = self._parse_annotation(node, pretty_arg_name)
                if annotation is None:
                    continue

                annotations[annotation.name] = annotation
            elif _ignore_node(node):
                pass
            else:
                self._issue_output('unknown-node',
                                   'Unknown node ‘%s’ in arg ‘%s’ of ‘%s’.' %
                                   (node.tag, pretty_arg_name, parent_name))

        type_parser = TypeParser(arg_type)
        type = type_parser.parse()
        if not type:
            self._issue_output('invalid-signature',
                               type_parser.get_output()[1])
            return None

        return ast.Argument(name, direction, type, annotations)

    def _parse_annotation(self, annotation_node, parent_name=None):
        """Parse an <annotation> element; return an ast.Annotation or None."""
        assert annotation_node.tag == 'annotation'

        if 'name' not in annotation_node.attrib:
            self._issue_output('missing-attribute',
                               'Missing required attribute ‘%s’ in '
                               'annotation.' % 'name')
            return None
        if 'value' not in annotation_node.attrib:
            self._issue_output('missing-attribute',
                               'Missing required attribute ‘%s’ in '
                               'annotation.' % 'value')
            return None

        name = annotation_node.attrib.get('name')
        value = annotation_node.attrib.get('value')

        for node in annotation_node.getchildren():
            if _ignore_node(node):
                pass
            else:
                self._issue_output('unknown-node',
                                   'Unknown node ‘%s’ in annotation '
                                   '‘%s.%s’.' % (node.tag, parent_name, name))

        return ast.Annotation(name, value)
