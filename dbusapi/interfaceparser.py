#!/usr/bin/python
# -*- coding: utf-8 -*-
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
try:
    from xml.etree import cElementTree as ElementTree
except ImportError:
    from xml.etree import ElementTree

from dbusapi import ast


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
        self._filename = os.path.abspath(filename)
        self._output = []

    def _ignore_node(self, node):
        # We definitely want to ignore:
        #  - {http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0}\
        #    docstring
        #  - {http://www.freedesktop.org/dbus/1.0/doc.dtd}doc
        return node.tag[0] == '{'  # in a namespace

    def _issue_output(self, message):
        self._output.append(message)

    def print_output(self):
        for message in self._output:
            sys.stderr.write('ERROR: %s\n' % message)

    def get_output(self):
        return self._output

    def parse(self):
        self._output = []
        tree = ElementTree.parse(self._filename)
        out = self._parse_root(tree.getroot())

        # Squash output on error.
        if len(self._output) != 0:
            return None

        return out

    def _parse_root(self, root):
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
            elif self._ignore_node(node):
                pass
            else:
                self._issue_output('Unrecognised node ‘%s’ in root.' %
                                   node.tag)

        return interfaces

    def _parse_interface(self, interface_node):
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
                    self._issue_output('Duplicate method definition '
                                       '‘%s.%s’.' % method.format_name())
                    continue

                methods[method.name] = method
            elif node.tag == 'signal':
                signal = self._parse_signal(node)
                if signal is None:
                    continue

                if signal.name in signals:
                    self._issue_output('Duplicate signal definition '
                                       '‘%s.%s’.' % signal.format_name())
                    continue

                signals[signal.name] = signal
            elif node.tag == 'property':
                prop = self._parse_property(node)
                if prop is None:
                    continue

                if prop.name in properties:
                    self._issue_output('Duplicate property definition '
                                       '‘%s.%s’.' % prop.format_name())
                    continue

                properties[prop.name] = prop
            elif node.tag == 'annotation':
                annotation = self._parse_annotation(node)
                if annotation is None:
                    continue

                annotations[annotation.name] = annotation
            elif self._ignore_node(node):
                pass
            else:
                self._issue_output('Unrecognised node ‘%s’ in interface '
                                   '‘%s’.' % (node.tag, name))

        return ast.ASTInterface(name, methods, properties, signals,
                                annotations)

    def _parse_method(self, method_node):
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
            elif self._ignore_node(node):
                pass
            else:
                self._issue_output('Unrecognised node ‘%s’ in method ‘%s’.' %
                                   (node.tag, name))

        return ast.ASTMethod(name, args, annotations)

    def _parse_signal(self, signal_node):
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
            elif self._ignore_node(node):
                pass
            else:
                self._issue_output('Unrecognised node ‘%s’ in signal ‘%s’.' %
                                   (node.tag, name))

        return ast.ASTSignal(name, args, annotations)

    def _parse_property(self, property_node):
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
            elif self._ignore_node(node):
                pass
            else:
                self._issue_output('Unrecognised node ‘%s’ in property ‘%s’.' %
                                   (node.tag, name))

        return ast.ASTProperty(name, prop_type, access, annotations)

    def _parse_arg(self, arg_node):
        assert arg_node.tag == 'arg'

        if 'type' not in arg_node.attrib:
            self._issue_output('Missing required attribute ‘%s’ in arg.' %
                               'type')
            return None

        name = arg_node.attrib.get('name', None)
        direction = arg_node.attrib.get('direction',
                                        ast.ASTArgument.DIRECTION_IN)
        arg_type = arg_node.attrib['type']
        annotations = {}

        for node in arg_node.getchildren():
            if node.tag == 'annotation':
                annotation = self._parse_annotation(node)
                if annotation is None:
                    continue

                annotations[annotation.name] = annotation
            elif self._ignore_node(node):
                pass
            else:
                self._issue_output('Unrecognised node ‘%s’ in arg ‘%s’.' %
                                   (node.tag, name))

        return ast.ASTArgument(name, direction, arg_type, annotations)

    def _parse_annotation(self, annotation_node):
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
            if self._ignore_node(node):
                pass
            else:
                self._issue_output('Unrecognised node ‘%s’ in annotation '
                                   '‘%s’.' % (node.tag, name))

        return ast.ASTAnnotation(name, value)
