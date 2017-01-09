# -*- coding: utf-8 -*-
#
# Copyright © 2015, 2016 Collabora Ltd.
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
An implementation of the abstract syntax tree (AST) for a D-Bus introspection
document, which fully describes a D-Bus API.

An AST can be built by parsing an XML file (using
`interfaceparser.InterfaceParser`) or by building the tree of objects manually.
"""


from abc import ABCMeta
from collections import OrderedDict
# pylint: disable=no-member
from lxml import etree
from re import match
from dbusapi.log import Log
from dbusapi.typeparser import TypeParser


TP_DTD = 'http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0'
FDO_DTD = 'http://www.freedesktop.org/dbus/1.0/doc.dtd'


class AstLog(Log):

    """Specialized Log subclass for AST messages"""

    def __init__(self):
        """Construct a new AstLog"""
        super(AstLog, self).__init__()
        self.register_issue_code('unknown-node')
        self.register_issue_code('empty-root')
        self.register_issue_code('missing-attribute')
        self.register_issue_code('duplicate-node')
        self.register_issue_code('duplicate-interface')
        self.register_issue_code('duplicate-method')
        self.register_issue_code('duplicate-signal')
        self.register_issue_code('duplicate-property')
        self.register_issue_code('node-name')
        self.register_issue_code('interface-name')
        self.register_issue_code('method-name')
        self.register_issue_code('signal-name')
        self.register_issue_code('property-type')
        self.register_issue_code('argument-type')
        self.domain = 'ast'


def ignore_node(node):
    """Decide whether to ignore the given node when parsing."""
    return node.tag[0] == '{'  # in a namespace


# pylint: disable=too-many-instance-attributes
class BaseNode(object):

    """Base class for all D-Bus AST nodes."""

    __metaclass__ = ABCMeta

    DOCSTRING_TAGS = ['{%s}docstring' % TP_DTD,
                      '{%s}doc' % FDO_DTD]

    required_attributes = ['name']
    optional_attributes = []

    def __init__(self, name, annotations=None, log=None):
        """Construct a new ast.BaseNode

        Args:
            name: str, the name of the node.
            annotations: potentially empty dict of annotations applied
                to the node, mapping annotation name to an `ast.Annotation`
                instance
            log: subclass of `Log`, used to store log messages; can be None
        """
        self.name = name
        self.children = []
        self.parent = None
        self._comment = None
        self.log = log or AstLog()
        self.annotations = OrderedDict()
        self.line_number = -1
        self.comment_line_number = -1

        self._children_types = {
            'annotation': Annotation,
        }
        self._type_containers = {
            Annotation: self.annotations,
        }

        for annotation in (annotations or {}).values():
            self._add_child(annotation)

    @classmethod
    def from_xml(cls, node, comment, log, parent=None):
        """Return a new ast.BaseNode instance from an XML node."""
        attrs = {}

        valid = True
        for attr_name in cls.required_attributes:
            # Avoid redefining a builtin
            member_name = attr_name
            if member_name == 'type':
                member_name = 'type_'

            try:
                attrs[member_name] = node.attrib[attr_name]
            except KeyError:
                log.log_issue('missing-attribute',
                              'Missing required attribute ‘%s’ in %s.' %
                              (attr_name, node.tag))
                valid = False

        if not valid:
            return None

        for attr_name in cls.optional_attributes:
            attrs[attr_name] = node.attrib.get(attr_name)

        # FIXME: Hack for the fact that Node.name and Argument.name are not
        # actually required, but is the first attribute in the constructor, and
        # hence must be specified. This can be removed when we break API.
        if (cls == Node or cls == Argument) and 'name' not in attrs:
            attrs['name'] = None
        elif issubclass(cls, Callable) and 'args' not in attrs:
            attrs['args'] = []

        attrs['log'] = log
        res = cls(**attrs)
        res.line_number = node.sourceline
        if comment is not None:
            res.comment = comment.text
            # lxml reports the last source line for xml comments as
            # being the actual source line, fix this.
            # Also report line numbers starting from 1, consistent
            # with node.line_number
            res.comment_line_number = (comment.sourceline -
                                       len(res.comment.split('\n')) + 1)

        if parent:
            parent.add_child(res)

        res.parse_xml_children(node)
        return res

    def add_child(self, child):
        """Add a child to the node"""
        return self._add_child(child)

    def parse_xml_children(self, node):
        """Parse the XML node's children."""
        xml_comment = None
        for elem in node:
            if elem.tag == etree.Comment:
                xml_comment = elem
                continue

            elif elem.tag in BaseNode.DOCSTRING_TAGS:
                self.comment_line_number = elem.sourceline
                self.comment = elem.text
                continue

            elif ignore_node(elem):
                xml_comment = None
                continue

            try:
                ctype = self._children_types[elem.tag]
            except KeyError:
                xml_comment = None
                if isinstance(self, Node) and not self.pretty_name:
                    # Special handling for root nodes to allow more meaningful
                    #   error messages.
                    self.__log_issue('unknown-node',
                                     "Unknown node ‘%s’ in root." % elem.tag)
                else:
                    self.__log_issue('unknown-node',
                                     "Unknown node ‘%s’ in %s ‘%s’." %
                                     (elem.tag, type(self).__name__.lower(),
                                      self.pretty_name))
                continue

            ctype.from_xml(elem, xml_comment, parent=self,
                           log=self.log)
            xml_comment = None

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
        """
        Get the comment for this node.

        Returns:
            str: If the node was annotated with `org.gtk.GDBus.DocString`,
                the value of the annotation, otherwise one of:
                * A tp:docstring child node
                * A doc:doc child node
                * An XML comment immediately preceding the XML node.
                , whichever is seen last.
        """
        try:
            doc_annotation = self.annotations['org.gtk.GDBus.DocString']
            return doc_annotation.value
        except KeyError:
            return self._comment

    @comment.setter
    def comment(self, value):
        """Set the comment for this node."""
        self._comment = value

    @property
    def pretty_name(self):
        """Format the node's name as a human-readable string."""
        return self.name

    def __log_issue(self, code, message):
        self.log.log_issue(code, message)

    def _child_is_duplicate(self, child):
        return child.name in self._type_containers[type(child)]

    def _add_child(self, child):
        child.parent = self
        if self._child_is_duplicate(child):
            self.__log_issue('duplicate-%s' % type(child).__name__.lower(),
                             'Duplicate %s definition ‘%s’.' %
                             (type(child).__name__.lower(), child.pretty_name))
            return False

        self.children.append(child)
        container = self._type_containers[type(child)]
        if isinstance(container, list):
            container.append(child)
        else:
            container[child.name] = child
        return True


class Node(BaseNode):

    """
    AST representation of a <node> element.

    This represents the top level of a D-Bus API.
    """

    required_attributes = []
    optional_attributes = ['name']

    # pylint: disable=too-many-arguments
    def __init__(self, name=None, interfaces=None, nodes=None,
                 annotations=None, log=None):
        """
        Construct a new ast.Node.

        Args:
            name: node name; a non-empty string; The root <node> should either
                have no name or should have a name that is a valid absolute
                object path. Child <node> names must be valid relative paths.
            interfaces: potentially empty dict of interfaces in the node,
                mapping interface name to an `ast.Interface` instance
            nodes: potentially empty dict of properties in the node,
                mapping node name to an `ast.Node` instance
            annotations: potentially empty dict of annotations applied to the
                node, mapping annotation name to an `ast.Annotation` instance
            log: subclass of `Log`, used to store log messages; can be None
        """
        super(Node, self).__init__(name, annotations, log)
        self._children_types.update({'interface': Interface,
                                     'node': Node})

        self.interfaces = OrderedDict()
        self.nodes = OrderedDict()

        self._type_containers.update({Interface: self.interfaces,
                                      Node: self.nodes})

        for child in (interfaces or {}).values():
            self._add_child(child)
        for child in (nodes or {}).values():
            self._add_child(child)

    def _add_child(self, child):
        if isinstance(child, Node):
            if not child.name:
                self.log.log_issue('missing-attribute',
                                   'Missing required attribute ‘name’ in '
                                   'non-root node.')
            elif not Node.is_valid_relative_object_path(child.name):
                self.log.log_issue('node-name',
                                   'Non-root node name is not a relative '
                                   'object path ‘%s’.' % child.name)
        child.node = self
        return super(Node, self)._add_child(child)

    @staticmethod
    def is_valid_absolute_object_path(path):
        """
        Validate an absolute D-Bus object path.

        https://dbus.freedesktop.org/doc/dbus-specification.html#message-protocol-marshaling-object-path

        Args:
            path: object path
        """
        return path == '/' or match(r'(/[A-Za-z0-9_]+)+', path) is not None

    @staticmethod
    def is_valid_relative_object_path(path):
        """
        Validate a relative D-Bus object path.

        https://dbus.freedesktop.org/doc/dbus-specification.html#message-protocol-marshaling-object-path

        Args:
            path: object path
        """
        return match(r'[A-Za-z0-9_]+(/[A-Za-z0-9_]+)*', path) is not None


class Interface(BaseNode):

    """
    AST representation of an <interface> element.

    This represents the most commonly used node of a D-Bus API.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, name, methods=None, properties=None,
                 signals=None, annotations=None, log=None):
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
            log: subclass of `Log`, used to store log messages; can be None
        """
        super(Interface, self).__init__(name, annotations, log)

        if name and not Interface.is_valid_interface_name(name):
            self.log.log_issue('interface-name',
                               'Invalid interface name ‘%s’.' % name)

        self._children_types.update({'signal': Signal,
                                     'method': Method,
                                     'property': Property})

        self.methods = OrderedDict()
        self.signals = OrderedDict()
        self.properties = OrderedDict()

        self._type_containers.update({Method: self.methods,
                                      Signal: self.signals,
                                      Property: self.properties})

        for child in (methods or {}).values():
            self._add_child(child)
        for child in (signals or {}).values():
            self._add_child(child)
        for child in (properties or {}).values():
            self._add_child(child)

    def _add_child(self, child):
        child.interface = self
        return super(Interface, self)._add_child(child)

    @staticmethod
    def is_valid_interface_name(name):
        """
        Validate a D-Bus interface name.

        http://dbus.freedesktop.org/doc/dbus-specification.html#message-protocol-names-interface

        Args:
            name: interface name
        """
        return len(name) <= 255 and \
            match(r'[A-Za-z_][A-Za-z0-9_]*'
                  r'(\.[A-Za-z_][A-Za-z0-9_]*)+', name) is not None


def _dotted_name(elem):
    if elem.parent:
        return elem.parent.format_name() + '.' + elem.name
    return elem.name


class Property(BaseNode):

    """
    AST representation of a <property> element.

    This represents a readable or writable property of an interface.
    """

    ACCESS_READ = 'read'
    ACCESS_WRITE = 'write'
    ACCESS_READWRITE = 'readwrite'

    required_attributes = BaseNode.required_attributes + ['access', 'type']

    # pylint: disable=too-many-arguments
    def __init__(self, name, type_, access, annotations=None, log=None):
        """
        Construct a new ast.Property.

        Args:
            name: property name; a non-empty string, not including the parent
                interface name
            type_: type string for the property; see http://goo.gl/uCpa5A
            access: ACCESS_READ, ACCESS_WRITE, or ACCESS_READWRITE
            annotations: potentially empty dict of annotations applied to the
                property, mapping annotation name to an `ast.Annotation`
                instance
            log: subclass of `Log`, used to store log messages; can be None
        """
        super(Property, self).__init__(name, annotations, log)

        type_parser = TypeParser(type_)
        self.type = type_parser.parse()
        if self.type is None:
            message = type_parser.get_output()[0][3]
            self.log.log_issue('property-type',
                               'Error when parsing type ‘%s’ for property '
                               '‘%s’: %s' %
                               (type_, name, message))

        self.access = access
        self.interface = None

    @property
    def pretty_name(self):
        """Format the property's name as a human-readable string"""
        return _dotted_name(self)


class Callable(BaseNode):

    u"""
    AST representation of a callable element.

    This represents a ‘callable’, such as a method or a signal. All callables
    contain a list of in and out arguments.
    """

    def __init__(self, name, args, annotations=None, log=None):
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
            log: subclass of `Log`, used to store log messages; can be None
        """
        super(Callable, self).__init__(name, annotations, log)
        self.arguments = []
        self.interface = None
        self._children_types.update({'arg': Argument})
        self._type_containers.update({Argument: self.arguments})

        for arg in args:
            self._add_child(arg)

    def _child_is_duplicate(self, child):
        if isinstance(child, Argument):
            return False
        return super(Callable, self)._child_is_duplicate(child)

    @property
    def pretty_name(self):
        """Format the callable's name as a human-readable string"""
        return _dotted_name(self)

    @staticmethod
    def is_valid_name(name):
        """
        Validate a D-Bus member name.

        https://dbus.freedesktop.org/doc/dbus-specification.html#message-protocol-names-member

        Args:
            name: callable name
        """
        return len(name) <= 255 and \
            match(r'[A-Za-z_][A-Za-z0-9_]*', name) is not None


class Method(Callable):

    """
    AST representation of a <method> element.

    This represents a callable method of an interface.
    """

    def __init__(self, name, args, annotations=None, log=None):
        """
        Construct a new ast.Method.

        Args:
            name: method name; a non-empty string, not including the parent
                interface name
            args: potentially empty ordered list of ast.Arguments accepted and
                returned by the method
            annotations: potentially empty dict of annotations applied to the
                method, mapping annotation name to an ast.Annotation
                instance
            log: subclass of `Log`, used to store log messages; can be None
        """
        super(Method, self).__init__(name, args, annotations, log)

        if name and not Callable.is_valid_name(name):
            self.log.log_issue('method-name',
                               'Invalid method name ‘%s’.' % name)


class Signal(Callable):

    """
    AST representation of a <signal> element.

    This represents an emittable signal on an interface.
    """

    def __init__(self, name, args, annotations=None, log=None):
        """
        Construct a new ast.Signal.

        Args:
            name: signal name; a non-empty string, not including the parent
                interface name
            args: potentially empty ordered list of ast.Arguments accepted and
                returned by the signal
            annotations: potentially empty dict of annotations applied to the
                signal, mapping annotation name to an ast.Annotation
                instance
            log: subclass of `Log`, used to store log messages; can be None
        """
        super(Signal, self).__init__(name, args, annotations, log)

        if name and not Callable.is_valid_name(name):
            self.log.log_issue('signal-name',
                               'Invalid signal name ‘%s’.' % name)


class Argument(BaseNode):

    """
    AST representation of an <arg> element.

    This represents an argument to an `ast.Signal` or `ast.Method`.
    """

    DIRECTION_IN = 'in'
    DIRECTION_OUT = 'out'

    required_attributes = ['type']
    optional_attributes = ['direction', 'name']

    # pylint: disable=too-many-arguments
    def __init__(self, name, direction, type_, annotations=None, log=None):
        """
        Construct a new ast.Argument.

        Args:
            name: argument name; may be empty
            direction: DIRECTION_IN or DIRECTION_OUT
            type_: type string for the argument; see http://goo.gl/uCpa5A
            annotations: potentially empty dict of annotations applied to the
                argument, mapping annotation name to an ast.Annotation
                instance
            log: subclass of `Log`, used to store log messages; can be None
        """
        super(Argument, self).__init__(name, annotations, log)

        type_parser = TypeParser(type_)
        self.type = type_parser.parse()
        if self.type is None:
            message = type_parser.get_output()[0][3]
            self.log.log_issue('argument-type',
                               'Error when parsing type ‘%s’ for argument '
                               '‘%s’: %s' %
                               (type_, name, message))

        self.direction = direction or Argument.DIRECTION_IN
        self._index = -1

    @property
    def pretty_name(self):
        """Format the argument's name as a human-readable string"""
        if self.index == -1 and self.name is None:
            res = 'unnamed'
        elif self.index == -1:
            res = '‘%s’' % self.name
        elif self.name is None:
            res = '%u' % self.index
        else:
            res = '%u (‘%s’)' % (self.index, self.name)

        if self.parent:
            parent_type = type(self.parent).__name__.lower()
            res += ' of %s ‘%s’' % (parent_type, self.parent.pretty_name)

        return res

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


class Annotation(BaseNode):

    """
    AST representation of an <annotation> element.

    This represents an arbitrary key-value metadata annotation attached to one
    of the nodes in an interface.
    The annotation name can be one of the well-known ones described at
    http://goo.gl/LgmNUe, or could be something else.
    """

    optional_attributes = ['value']

    def __init__(self, name, value=None, log=None):
        """
        Construct a new ast.Annotation.

        Args:
            name: annotation name; a non-empty string
            value: annotation value; any string is permitted
            log: subclass of `Log`, used to store log messages; can be None
        """
        super(Annotation, self).__init__(name, log=log)
        self.value = value

    @property
    def pretty_name(self):
        """Format the annotation's name as a human-readable string"""
        if not self.parent:
            return self.name
        return '%s of ‘%s’' % (self.name, self.parent.pretty_name)
