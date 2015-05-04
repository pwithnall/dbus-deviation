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


# pylint: disable=too-few-public-methods


# pylint: disable=interface-not-implemented
class Interface(object):

    """
    AST representation of an <interface> element.

    This represents the top level of a D-Bus API.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, name, methods=None, properties=None,
                 signals=None, annotations=None):
        """
        Construct a new ast.Interface.

        Args:
            name: interface name; a non-empty string
            methods: potentially empty dict of methods in the interface,
                mapping method name to an ast.Method instance
            properties: potentially empty dict of properties in the interface,
                mapping property name to an ast.Property instance
            signals: potentially empty dict of signals in the interface,
                mapping signal name to an ast.Signal instance
            annotations: potentially empty dict of annotations applied to the
                interface, mapping annotation name to an ast.Annotation
                instance
        """
        if methods is None:
            methods = {}
        if properties is None:
            properties = {}
        if signals is None:
            signals = {}
        if annotations is None:
            annotations = {}


        self.name = name
        self.methods = methods
        self.properties = properties
        self.signals = signals
        self.annotations = annotations

        for method in self.methods.values():
            method.interface = self
        for prop in self.properties.values():
            prop.interface = self
        for signal in self.signals.values():
            signal.interface = self
        for annotation in self.annotations.values():
            annotation.parent = self

    def format_name(self):
        u"""Format the interface’s name as a human-readable string."""
        return self.name


class Property(object):

    """
    AST representation of a <property> element.

    This represents a readable or writable property of an interface.
    """

    ACCESS_READ = 'read'
    ACCESS_WRITE = 'write'
    ACCESS_READWRITE = 'readwrite'

    def __init__(self, name, prop_type, access, annotations=None):
        """
        Construct a new ast.Property.

        Args:
            name: property name; a non-empty string, not including the parent
                interface name
            prop_type: type string for the property; see http://goo.gl/uCpa5A
            access: ACCESS_READ, ACCESS_WRITE, or ACCESS_READWRITE
            annotations: potentially empty dict of annotations applied to the
                property, mapping annotation name to an ast.Annotation
                instance
        """
        if annotations is None:
            annotations = {}

        self.name = name
        self.type = prop_type
        self.access = access
        self.interface = None
        self.annotations = annotations
        for annotation in self.annotations.values():
            annotation.parent = self

    def format_name(self):
        u"""Format the property’s name as a human-readable string."""
        if self.interface is None:
            return self.name
        return '%s.%s' % (self.interface.format_name(), self.name)


class Callable(object):

    u"""
    AST representation of a callable element.

    This represents a ‘callable’, such as a method or a signal. All callables
    contain a list of in and out arguments.
    """

    def __init__(self, name, args, annotations=None):
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
        if annotations is None:
            annotations = {}

        self.name = name
        self.arguments = args
        self.annotations = annotations
        for annotation in self.annotations.values():
            annotation.parent = self

        i = 0
        for arg in self.arguments:
            arg.parent = self
            arg.index = i
            i += 1


class Method(Callable):

    """
    AST representation of a <method> element.

    This represents a callable method of an interface.
    """

    def __init__(self, name, args, annotations=None):
        """
        Construct a new ast.Method.

        Args:
            name: method name; a non-empty string, not including the parent
                interface name
            args: potentially empty ordered list of ast.Arguments accepted and
                returned by the method
            annotations: potentially empty dict of annotations applied to the
                method, mapping annotation name to an ast.Annotation instance
        """
        if annotations is None:
            annotations = {}

        Callable.__init__(self, name, args, annotations)
        self.interface = None

    def format_name(self):
        u"""Format the method’s name as a human-readable string."""
        if self.interface is None:
            return self.name
        return '%s.%s' % (self.interface.format_name(), self.name)


class Signal(Callable):

    """
    AST representation of a <signal> element.

    This represents an emittable signal on an interface.
    """

    def __init__(self, name, args, annotations=None):
        """
        Construct a new ast.Signal.

        Args:
            name: annotation name; a non-empty string, not including the
                parent interface name
            args: potentially empty ordered list of ast.Arguments provided by
                the signal
            annotations: potentially empty dict of annotations applied to the
                signal, mapping annotation name to an ast.Annotation instance
        """
        if annotations is None:
            annotations = {}

        Callable.__init__(self, name, args, annotations)
        self.interface = None

    def format_name(self):
        u"""Format the signal’s name as a human-readable string."""
        if self.interface is None:
            return self.name
        return '%s.%s' % (self.interface.format_name(), self.name)


class Argument(object):

    """
    AST representation of an <arg> element.

    This represents an argument to an ast.Signal or ast.Method.
    """

    DIRECTION_IN = 'in'
    DIRECTION_OUT = 'out'

    def __init__(self, name, direction, arg_type, annotations=None):
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
        if annotations is None:
            annotations = {}

        self.name = name
        self.direction = direction
        self.type = arg_type
        self.index = -1
        self.parent = None
        self.annotations = annotations
        for annotation in self.annotations.values():
            annotation.parent = self

    def format_name(self):
        u"""Format the argument’s name as a human-readable string."""
        if self.index == -1 and self.name is None:
            return 'unnamed'
        elif self.index == -1:
            return '‘%s’' % self.name
        elif self.name is None:
            return '%u' % self.index
        else:
            return '%u (‘%s’)' % (self.index, self.name)


class Annotation(object):

    u"""
    AST representation of an <annotation> element.

    This represents an arbitrary key–value metadata annotation attached to one
    of the nodes in an interface.

    The annotation name can be one of the well-known ones described at
    http://goo.gl/LgmNUe, or could be something else.
    """

    def __init__(self, name, value):
        """
        Construct a new ast.Annotation.

        Args:
            name: annotation name; a non-empty string
            value: annotation value; any string is permitted
        """
        self.name = name
        self.value = value
        self.parent = None

    def format_name(self):
        u"""Format the annotation’s name as a human-readable string."""
        if self.parent is None:
            return self.name
        return '%s.%s' % (self.parent.format_name(), self.name)
