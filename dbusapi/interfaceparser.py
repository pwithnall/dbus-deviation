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
import sys

# PyPy support
# pylint: disable=interface-not-implemented
try:
    from xml.etree import cElementTree as ElementTree
except ImportError:
    from xml.etree import ElementTree

from dbusapi import ast


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

    def _issue_output(self, message):
        """Append a message to the parser output."""
        self._output.append((self._filename, 'parser', 'parser', message))

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
        if len(self._output) != 0:
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
        interfaces = {}

        if root.tag != 'node':
            self._issue_output('Unrecognised root node ‘%s’.' % root.tag)
            return interfaces

        for node in root.getchildren():
            if node.tag == 'interface':
                interface = self._parse_interface(node)
                if interface is None:
                    continue

                if interface.name in interfaces:
                    self._issue_output('Duplicate interface definition '
                                       '‘%s’.' % interface.format_name())
                    continue

                interfaces[interface.name] = interface
            elif _ignore_node(node):
                pass
            else:
                self._issue_output('Unrecognised node ‘%s’ in root.' %
                                   node.tag)

        return interfaces

    # pylint: disable=too-many-branches
    def _parse_interface(self, interface_node):  # noqa
        """Parse an <interface> element; return an ast.Interface or None."""
        assert interface_node.tag == 'interface'

        if 'name' not in interface_node.attrib:
            self._issue_output('Missing required attribute ‘%s’ in '
                               'interface.' % 'name')
            return None

        name = interface_node.attrib['name']
        methods = {}
        signals = {}
        properties = {}
        annotations = {}

        for node in interface_node.getchildren():
            if node.tag == 'method':
                method = self._parse_method(node)
                if method is None:
                    continue

                if method.name in methods:
                    self._issue_output('Duplicate method definition ‘%s’.' %
                                       method.format_name())
                    continue

                methods[method.name] = method
            elif node.tag == 'signal':
                signal = self._parse_signal(node)
                if signal is None:
                    continue

                if signal.name in signals:
                    self._issue_output('Duplicate signal definition ‘%s’.' %
                                       signal.format_name())
                    continue

                signals[signal.name] = signal
            elif node.tag == 'property':
                prop = self._parse_property(node)
                if prop is None:
                    continue

                if prop.name in properties:
                    self._issue_output('Duplicate property definition ‘%s’.' %
                                       prop.format_name())
                    continue

                properties[prop.name] = prop
            elif node.tag == 'annotation':
                annotation = self._parse_annotation(node)
                if annotation is None:
                    continue

                annotations[annotation.name] = annotation
            elif _ignore_node(node):
                pass
            else:
                self._issue_output('Unrecognised node ‘%s’ in interface '
                                   '‘%s’.' % (node.tag, name))

        return ast.Interface(name, methods, properties, signals,
                             annotations)

    def _parse_method(self, method_node):
        """Parse a <method> element; return an ast.Method or None."""
        assert method_node.tag == 'method'

        if 'name' not in method_node.attrib:
            self._issue_output('Missing required attribute ‘%s’ in method.' %
                               'name')
            return None

        name = method_node.attrib['name']
        args = []
        annotations = {}

        for node in method_node.getchildren():
            if node.tag == 'arg':
                arg = self._parse_arg(node)
                if arg is None:
                    continue

                args.append(arg)
            elif node.tag == 'annotation':
                annotation = self._parse_annotation(node)
                if annotation is None:
                    continue

                annotations[annotation.name] = annotation
            elif _ignore_node(node):
                pass
            else:
                self._issue_output('Unrecognised node ‘%s’ in method ‘%s’.' %
                                   (node.tag, name))

        return ast.Method(name, args, annotations)

    def _parse_signal(self, signal_node):
        """Parse a <signal> element; return an ast.Signal or None."""
        assert signal_node.tag == 'signal'

        if 'name' not in signal_node.attrib:
            self._issue_output('Missing required attribute ‘%s’ in signal.' %
                               'name')
            return None

        name = signal_node.attrib['name']
        args = []
        annotations = {}

        for node in signal_node.getchildren():
            if node.tag == 'arg':
                arg = self._parse_arg(node)
                if arg is None:
                    continue

                args.append(arg)
            elif node.tag == 'annotation':
                annotation = self._parse_annotation(node)
                if annotation is None:
                    continue

                annotations[annotation.name] = annotation
            elif _ignore_node(node):
                pass
            else:
                self._issue_output('Unrecognised node ‘%s’ in signal ‘%s’.' %
                                   (node.tag, name))

        return ast.Signal(name, args, annotations)

    def _parse_property(self, property_node):
        """Parse a <property> element; return an ast.Property or None."""
        assert property_node.tag == 'property'

        if 'name' not in property_node.attrib:
            self._issue_output('Missing required attribute ‘%s’ in property.' %
                               'name')
            return None
        elif 'type' not in property_node.attrib:
            self._issue_output('Missing required attribute ‘%s’ in property.' %
                               'type')
            return None
        elif 'access' not in property_node.attrib:
            self._issue_output('Missing required attribute ‘%s’ in property.' %
                               'access')
            return None

        name = property_node.attrib['name']
        prop_type = property_node.attrib['type']
        access = property_node.attrib['access']
        annotations = {}

        for node in property_node.getchildren():
            if node.tag == 'annotation':
                annotation = self._parse_annotation(node)
                if annotation is None:
                    continue

                annotations[annotation.name] = annotation
            elif _ignore_node(node):
                pass
            else:
                self._issue_output('Unrecognised node ‘%s’ in property ‘%s’.' %
                                   (node.tag, name))

        return ast.Property(name, prop_type, access, annotations)

    def _parse_arg(self, arg_node):
        """Parse an <arg> element; return an ast.Argument or None."""
        assert arg_node.tag == 'arg'

        if 'type' not in arg_node.attrib:
            self._issue_output('Missing required attribute ‘%s’ in arg.' %
                               'type')
            return None

        name = arg_node.attrib.get('name', None)
        direction = arg_node.attrib.get('direction',
                                        ast.Argument.DIRECTION_IN)
        arg_type = arg_node.attrib['type']
        annotations = {}

        for node in arg_node.getchildren():
            if node.tag == 'annotation':
                annotation = self._parse_annotation(node)
                if annotation is None:
                    continue

                annotations[annotation.name] = annotation
            elif _ignore_node(node):
                pass
            else:
                self._issue_output('Unrecognised node ‘%s’ in arg ‘%s’.' %
                                   (node.tag, name))

        return ast.Argument(name, direction, arg_type, annotations)

    def _parse_annotation(self, annotation_node):
        """Parse an <annotation> element; return an ast.Annotation or None."""
        assert annotation_node.tag == 'annotation'

        if 'name' not in annotation_node.attrib:
            self._issue_output('Missing required attribute ‘%s’ in '
                               'annotation.' % 'name')
            return None
        if 'value' not in annotation_node.attrib:
            self._issue_output('Missing required attribute ‘%s’ in '
                               'annotation.' % 'value')
            return None

        name = annotation_node.attrib.get('name')
        value = annotation_node.attrib.get('value')

        for node in annotation_node.getchildren():
            if _ignore_node(node):
                pass
            else:
                self._issue_output('Unrecognised node ‘%s’ in annotation '
                                   '‘%s’.' % (node.tag, name))

        return ast.Annotation(name, value)
