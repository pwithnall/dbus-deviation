# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
#
# Copyright © 2015, 2016 Collabora Ltd.
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


"""Implements a D-Bus ast."""


from collections import OrderedDict
# pylint: disable=no-member
from lxml import etree


TP_DTD = 'http://telepathy.freedesktop.org/wiki/DbusSpec#extensions-v0'
FDO_DTD = 'http://www.freedesktop.org/dbus/1.0/doc.dtd'


class Log(object):

    """Base logging class."""

    def __init__(self):
        """Construct a new Log"""
        self.issues = []
        self.issue_codes = set()
        self.domain = 'default'

    def register_issue_code(self, code):
        """
        Register a new issue code.

        Duplicate codes will be silently ignored.

        Args:
            code: str, an issue code, for example `unknown-node`
        """
        self.issue_codes.add(code)

    def log_issue(self, code, message):
        """
        Log a new issue.

        Args:
            code: str, A registered code for that issue.
            message: str, A message describing the issue.
        """
        assert code in self.issue_codes
        self.issues.append(self._create_entry(code, message))

    # pylint: disable=no-self-use
    def _create_entry(self, code, message):
        return (None, self.domain, code, message)


class AstLog(Log):

    """Specialized Log subclass for ast messages"""

    def __init__(self):
        """Construct a new AstLog"""
        super(AstLog, self).__init__()
        self.register_issue_code('unknown-node')
        self.register_issue_code('empty-root')
        self.register_issue_code('missing-attribute')
        self.register_issue_code('duplicate-interface')
        self.register_issue_code('duplicate-method')
        self.register_issue_code('duplicate-signal')
        self.register_issue_code('duplicate-property')
        self.domain = 'ast'


def ignore_node(node):
    """Decide whether to ignore the given node when parsing."""
    return node.tag[0] == '{'  # in a namespace


# pylint: disable=too-many-instance-attributes
class Node(object):

    """Base class for all D-Bus Ast nodes."""

    DOCSTRING_TAGS = ['{%s}docstring' % TP_DTD,
                      '{%s}doc' % FDO_DTD]

    required_attributes = ['name']
    optional_attributes = []

    def __init__(self, name, annotations=None, log=None):
        """Construct a new ast.Node

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
        """Return a new ast.Node instance from an XML node."""
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

        # FIXME: Hack for the fact that Argument.name is not actually required,
        # but is the first attribute in the constructor, and hence must be
        # specified. This can be removed when we break API.
        if cls == Argument and 'name' not in attrs:
            attrs['name'] = None
        elif issubclass(cls, Callable) and 'args' not in attrs:
            attrs['args'] = []

        attrs['log'] = log
        res = cls(**attrs)
        res.comment = comment

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
                xml_comment = elem.text
                continue

            elif elem.tag in Node.DOCSTRING_TAGS:
                self.comment = elem.text
                continue

            elif ignore_node(elem):
                xml_comment = None
                continue

            try:
                ctype = self._children_types[elem.tag]
            except KeyError:
                xml_comment = None
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


class Interface(Node):

    """
    AST representation of an <interface> element.

    This represents the top level of a D-Bus API.
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
        return super(Interface, self)._add_child(child)


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

    required_attributes = Node.required_attributes + ['access', 'type']

    # pylint: disable=too-many-arguments
    def __init__(self, name, type_, access, annotations=None, log=None):
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
            log: subclass of `Log`, used to store log messages; can be None
        """
        super(Property, self).__init__(name, annotations, log)
        self.type = type_
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
        self.direction = direction or Argument.DIRECTION_IN
        self.type = type_
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


class Annotation(Node):

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
