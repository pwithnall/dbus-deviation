#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
#
# Copyright © 2016 Collabora Ltd.
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


"""Implements a D-Bus ast, and a XML parsing function."""


from collections import OrderedDict
# pylint: disable=no-member
from lxml import etree


TP_DTD = 'http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0'
FDO_DTD = 'http://www.freedesktop.org/dbus/1.0/doc.dtd'


class DBusParsingError(Exception):

    """Error thrown when parsing a D-Bus interface XML fails"""

    pass


class DuplicateNodeError(DBusParsingError):

    """Error thrown when a duplicate node is found."""

    pass


class UnknownNodeError(DBusParsingError):

    """Error thrown when an unexpected node is found."""

    pass


class MissingAttributeError(DBusParsingError):

    """Error thrown when a required attribute is missing"""

    pass


def _ignore_node(node):
    """
    Decide whether to ignore the given node when parsing.

    We definitely want to ignore:
     * {http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0}docstring
     * {http://www.freedesktop.org/dbus/1.0/doc.dtd}doc
    """
    return node.tag[0] == '{'  # in a namespace


class Loggable(object):

    """Subclasses can inherit from this class to report recoverable errors."""

    (ERROR,
     WARNING) = range(2)

    __error_type_to_exception = {
            'unknown-node': UnknownNodeError,
            'missing-attribute': MissingAttributeError,
            'duplicate-interface': DuplicateNodeError,
            'duplicate-method': DuplicateNodeError,
            'duplicate-signal': DuplicateNodeError,
            'duplicate-property': DuplicateNodeError,
    }

    log = []
    recover = False
    filename = ''

    @staticmethod
    def get_error_codes():
        """Return a list of all possible error codes."""
        return Loggable.__error_type_to_exception.keys()

    @staticmethod
    def error(code, message, domain=''):
        """Call this to either raise an exception, or store the error."""
        if Loggable.recover:
            Loggable.log.append(
                (Loggable.filename, domain, code, message))
        else:
            raise Loggable.__error_type_to_exception[code](message)

    @staticmethod
    def reset():
        """Reset the log."""
        Loggable.log = []
        Loggable.recover = False
        Loggable.filename = ''

    @staticmethod
    def set_filename(filename):
        """Set the current filename."""
        Loggable.filename = filename


class Node(Loggable):

    """Base class for all D-Bus Ast nodes."""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, name=None, annotations=None):
        """Construct a new ast.Node

        Args:
            name: str, the name of the node.
            annotations: potentially empty dict of annotations applied
                to the node, mapping annotation name to an `ast.Annotation`
                instance
        """
        self.name = name
        self.children = []
        self.parent = None
        self._comment = None
        self.annotations = OrderedDict()

        self._children_types = {
                'annotation': Annotation,
        }
        self._type_containers = {
                Annotation: self.annotations,
        }
        self._required_attributes = {
                'name': 'name',
        }
        self._optional_attributes = {
        }

        for annotation in (annotations or {}).values():
            self._add_child(annotation)

    def __lookup_attributes(self, node):
        for attr_name, attr_storage in self._required_attributes.items():
            try:
                setattr(self, attr_storage, node.attrib[attr_name])
            except KeyError:
                self.error('missing-attribute',
                           'Missing required attribute ‘%s’ in %s.' %
                           (attr_name, node.tag),
                           'parser')
                continue

        for attr_name, attr_storage in self._optional_attributes.items():
            try:
                setattr(self, attr_storage, node.attrib[attr_name])
            except KeyError:
                pass

    @classmethod
    def from_xml(cls, node, comment=None):
        """Return a new ast.Node instance from an XML node."""
        res = cls()
        res.comment = comment
        res.parse(node)
        return res

    def _child_is_duplicate(self, child):
        return child.name in self._type_containers[type(child)]

    def _add_child(self, child):
        child.parent = self
        if self._child_is_duplicate(child):
            self.error('duplicate-%s' % type(child).__name__.lower(),
                       'Duplicate %s definition ‘%s’.' %
                       (type(child).__name__.lower(), child.pretty_name),
                       'parser')
            return

        self.children.append(child)
        container = self._type_containers[type(child)]
        # pylint: disable = unidiomatic-typecheck
        if type(container) == list:
            container.append(child)
        else:
            container[child.name] = child

    def parse(self, node):
        """Actually parse the XML node."""
        self.__lookup_attributes(node)

        xml_comment = None
        for elem in node:
            if elem.tag == etree.Comment:
                xml_comment = elem.text
                continue

            elif elem.tag == '{%s}docstring' % TP_DTD:
                self.comment = elem.text
                continue

            elif elem.tag == '{%s}doc' % FDO_DTD:
                self.comment = elem.text
                continue

            elif _ignore_node(elem):
                xml_comment = None
                continue

            try:
                ctype = self._children_types[elem.tag]
            except KeyError:
                xml_comment = None
                self.error('unknown-node',
                           "Unknown node ‘%s’ in %s ‘%s’." %
                           (elem.tag, type(self).__name__.lower(),
                            self.pretty_name),
                           'parser')
                continue

            child = ctype.from_xml(elem, xml_comment)
            xml_comment = None
            self._add_child(child)

    def walk(self):
        """Traverse this node's children in pre-order."""
        for child in self.children:
            yield child
            for grandchild in child.walk():
                yield grandchild

    # Backward compat
    def format_name(self):
        """Format this node's name as a human-readable string"""
        return self.pretty_name

    @property
    def comment(self):
        """Return the comment for this node."""
        try:
            doc_annotation = self.annotations.get('org.gtk.GDBus.DocString')
            if doc_annotation:
                return doc_annotation.value
        except AttributeError:
            pass

        return self._comment

    @comment.setter
    def comment(self, value):
        """Set the comment for this node."""
        self._comment = value

    @property
    def pretty_name(self):
        """Format the node's name as a human-readable string."""
        return self.name

    @property
    def level(self):
        """Return the level of this node in the Ast."""
        level = 0
        parent = self
        while parent:
            level += 1
            parent = parent.parent
        return level


class Interface(Node):

    """
    AST representation of an <interface> element.

    This represents the top level of a D-Bus API.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, name=None, methods=None, properties=None,
                 signals=None, annotations=None):
        """
        Construct a new ast.Interface.

        Args:
            name: interface name; a non-empty string
            methods: potentially empty dict of methods in the interface,
                mapping method name to an `ast.Method` instance
            properties: potentially empty dict of properties in the interface,
                mapping property name to an `ast.Property` instance
            signals: potentially empty dict of signals in the interface,
                mapping signal name to an `ast.Signal` instance
            annotations: potentially empty dict of annotations applied to the
                interface, mapping annotation name to an `ast.Annotation`
                instance
        """
        super(Interface, self).__init__(name, annotations)
        self._children_types.update({'signal': Signal,
                                     'method': Method,
                                     'property': Property})

        self.methods = OrderedDict()
        self.signals = OrderedDict()
        self.properties = OrderedDict()

        self._type_containers.update({Method: self.methods,
                                      Signal: self.signals,
                                      Property: self.properties})

        for child in (methods or {}).values() + (signals or {}).values() + \
                (properties or {}).values():
            self._add_child(child)

    def _add_child(self, child):
        child.interface = self
        super(Interface, self)._add_child(child)


def _dotted_name(elem):
    if elem.parent:
        return elem.parent.format_name() + '.' + elem.name
    return elem.name


class Property(Node):

    """
    AST representation of a <property> element.

    This represents a readable or writable property of an interface.
    """

    ACCESS_READ = 'read'
    ACCESS_WRITE = 'write'
    ACCESS_READWRITE = 'readwrite'

    def __init__(self, name=None, prop_type=None, access=None,
                 annotations=None):
        """
        Construct a new ast.Property.

        Args:
            name: property name; a non-empty string, not including the parent
                interface name
            prop_type: type string for the property; see http://goo.gl/uCpa5A
            access: ACCESS_READ, ACCESS_WRITE, or ACCESS_READWRITE
            annotations: potentially empty dict of annotations applied to the
                property, mapping annotation name to an `ast.Annotation`
                instance
        """
        super(Property, self).__init__(name, annotations)
        self._required_attributes.update({'access': 'access',
                                          'type': 'type'})
        self.type = prop_type
        self.access = access
        self.interface = None

    @property
    def pretty_name(self):
        """Format the property's name as a human-readable string"""
        return _dotted_name(self)


class Callable(Node):

    u"""
    AST representation of a callable element.

    This represents a ‘callable’, such as a method or a signal. All callables
    contain a list of in and out arguments.
    """

    def __init__(self, name=None, args=None, annotations=None):
        """
        Construct a new ast.Callable.

        Args:
            name: callable name; a non-empty string, not including the parent
                interface name
            args: potentially empty ordered list of ast.Arguments accepted and
                returned by the callable
            annotations: potentially empty dict of annotations applied to the
                callable, mapping annotation name to an ast.Annotation
                instance
        """
        super(Callable, self).__init__(name, annotations)
        self.arguments = []
        self.interface = None
        self._children_types.update({'arg': Argument})
        self._type_containers.update({Argument: self.arguments})

        for arg in args or []:
            self._add_child(arg)

    def _child_is_duplicate(self, child):
        # pylint: disable=unidiomatic-typecheck
        if type(child) == Argument:
            return False
        return super(Callable, self)._child_is_duplicate(child)

    def _add_child(self, child):
        super(Callable, self)._add_child(child)

    @property
    def pretty_name(self):
        """Format the callable's name as a human-readable string"""
        return _dotted_name(self)


class Method(Callable):

    """
    AST representation of a <method> element.

    This represents a callable method of an interface.
    """

    pass


class Signal(Callable):

    """
    AST representation of a <signal> element.

    This represents an emittable signal on an interface.
    """

    pass


class Argument(Node):

    """
    AST representation of an <arg> element.

    This represents an argument to an `ast.Signal` or `ast.Method`.
    """

    DIRECTION_IN = 'in'
    DIRECTION_OUT = 'out'

    def __init__(self, name=None, direction=None,
                 arg_type=None, annotations=None):
        """
        Construct a new ast.Argument.

        Args:
            name: argument name; may be empty
            direction: DIRECTION_IN or DIRECTION_OUT
            arg_type: type string for the argument; see http://goo.gl/uCpa5A
            annotations: potentially empty dict of annotations applied to the
                argument, mapping annotation name to an ast.Annotation
                instance
        """
        super(Argument, self).__init__(name, annotations)
        self.direction = direction or Argument.DIRECTION_IN
        self.type = arg_type
        self._index = -1
        self._required_attributes = {'type': 'type'}
        self._optional_attributes.update({'direction': 'direction',
                                          'name': 'name'})

    @property
    def pretty_name(self):
        """Format the argument's name as a human-readable string"""
        if self.index == -1 and self.name is None:
            return 'unnamed'
        elif self.index == -1:
            return '‘%s’' % self.name
        elif self.name is None:
            return '%u' % self.index
        else:
            return '%u (‘%s’)' % (self.index, self.name)

    @property
    def index(self):
        """The index of this argument in its parent's list of arguments"""
        # Slight optimization, assumes arguments cannot be reparented
        if self._index != -1:
            return self._index
        if not self.parent:
            return -1
        else:
            self._index = self.parent.arguments.index(self)
            return self._index


class Annotation(Node):

    """
    AST representation of an <annotation> element.

    This represents an arbitrary key-value metadata annotation attached to one
    of the nodes in an interface.
    The annotation name can be one of the well-known ones described at
    http://goo.gl/LgmNUe, or could be something else.
    """

    def __init__(self, name=None, value=None):
        """
        Construct a new ast.Annotation.

        Args:
            name: annotation name; a non-empty string
            value: annotation value; any string is permitted
        """
        super(Annotation, self).__init__(name)
        self.value = value
        self._required_attributes.update({'value': 'value'})

    @property
    def pretty_name(self):
        """Format the annotation's name as a human-readable string"""
        return _dotted_name(self)


def _skip_non_node(elem):
    for node in elem.getchildren():
        if node.tag == 'node':
            return node

    return None


def parse(filename, recover=False):
    """
    Parse an XML file and returns the root of the D-Bus ast.

    Args:
        filename: str, the file to parse
        recover: bool, whether to parse the XML file entirely
            when errors are encountered
    """
    Loggable.set_filename(filename)
    Loggable.recover = recover
    root = etree.parse(filename).getroot()
    interfaces = {}

    last_log_position = len(Loggable.log)

    # Handle specifications wrapped in tp:spec.
    if root.tag == '{%s}spec' % TP_DTD:
        root = _skip_non_node(root)

    if root.tag != 'node':
        Loggable.error('unknown-node',
                       'Unknown root node ‘%s’.' % root.tag)
        root = _skip_non_node(root)

    if root is None:
        return None

    xml_comment = None
    for elem in root:
        if elem.tag == etree.Comment:
            xml_comment = elem.text
        elif elem.tag == 'interface':
            interface = Interface.from_xml(elem, comment=xml_comment)
            if interface.name in interfaces:
                Loggable.error('duplicate-interface',
                               'Duplicate interface definition ‘%s’.' %
                               interface.name)
                continue
            interfaces[interface.name] = interface
            xml_comment = None
        elif _ignore_node(elem):
            xml_comment = None
        else:
            Loggable.error('unknown-node',
                           "Unknown node ‘%s’ in root." % elem.tag)

    log = Loggable.log[last_log_position:]

    if log:
        return None, log
    return interfaces, None
