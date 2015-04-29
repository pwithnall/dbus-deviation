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


# pylint: disable=too-few-public-methods


# pylint: disable=interface-not-implemented
class ASTInterface(object):
    """
    AST representation of an <interface> element.
    """
    # pylint: disable=too-many-arguments
    def __init__(self, name, methods, properties, signals, annotations):
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
        return self.name


class ASTProperty(object):
    """
    AST representation of a <property> element.
    """
    ACCESS_READ = 'read'
    ACCESS_WRITE = 'write'
    ACCESS_READWRITE = 'readwrite'

    def __init__(self, name, prop_type, access, annotations):
        self.name = name
        self.type = prop_type
        self.access = access
        self.interface = None
        self.annotations = annotations
        for annotation in self.annotations.values():
            annotation.parent = self

    def format_name(self):
        if self.interface is None:
            return self.name
        return '%s.%s' % (self.interface.format_name(), self.name)


class ASTCallable(object):
    """
    AST representation of an element which can contain <arg>s, such as a
    <method> or <signal>.
    """
    def __init__(self, name, args, annotations):
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


class ASTMethod(ASTCallable):
    """
    AST representation of a <method> element.
    """
    def __init__(self, name, args, annotations):
        ASTCallable.__init__(self, name, args, annotations)
        self.interface = None

    def format_name(self):
        if self.interface is None:
            return self.name
        return '%s.%s' % (self.interface.format_name(), self.name)


class ASTSignal(ASTCallable):
    """
    AST representation of a <signal> element.
    """
    def __init__(self, name, args, annotations):
        ASTCallable.__init__(self, name, args, annotations)
        self.interface = None

    def format_name(self):
        if self.interface is None:
            return self.name
        return '%s.%s' % (self.interface.format_name(), self.name)


class ASTArgument(object):
    """
    AST representation of an <arg> element.
    """
    DIRECTION_IN = 'in'
    DIRECTION_OUT = 'out'

    def __init__(self, name, direction, arg_type, annotations):
        self.name = name
        self.direction = direction
        self.type = arg_type
        self.index = -1
        self.parent = None
        self.annotations = annotations
        for annotation in self.annotations.values():
            annotation.parent = self

    def format_name(self):
        if self.index == -1 and self.name is None:
            return 'unnamed'
        elif self.name is None:
            return '%u' % self.index
        else:
            return '%u (‘%s’)' % (self.index, self.name)


class ASTAnnotation(object):
    """
    AST representation of an <annotation> element.
    """

    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.parent = None

    def format_name(self):
        if self.parent is None:
            return self.name
        return '%s.%s' % (self.parent.format_name(), self.name)
