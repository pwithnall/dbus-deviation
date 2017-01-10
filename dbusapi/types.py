# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
#
# Copyright © 2016 Kaloyan Tenchov
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
A representation of the D-Bus type system as a series of classes which can be
built into an abstract syntax tree (AST) for representing complex (nested)
types.

An AST can be built by parsing a D-Bus type signature (using
`typeparser.TypeParser`) or by building the tree of objects manually.
"""


from abc import ABCMeta, abstractmethod


# pylint: disable=too-few-public-methods
class Type(object):
    """
    An abstract class - AST representation of a D-Bus type.

    See http://dbus.freedesktop.org/doc/dbus-specification.html#type-system
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        """Constructor."""
        self.type = "\0"
        self.name = "INVALID"
        self.alignment = 1

    def __str__(self):
        """Format the type as a human-readable string."""
        return self.type

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)


# pylint: disable=too-few-public-methods
class Byte(Type):
    """
    AST representation of the D-Bus BYTE type.

    8-bit unsigned integer.
    """

    def __init__(self):
        """Constructor."""
        Type.__init__(self)
        self.type = "y"
        self.name = "BYTE"
        self.alignment = 1


# pylint: disable=too-few-public-methods
class Boolean(Type):
    """
    AST representation of the D-Bus BOOLEAN type.

    Boolean value, 0 is FALSE and 1 is TRUE. Everything else is invalid.
    """

    def __init__(self):
        """Constructor."""
        Type.__init__(self)
        self.type = "b"
        self.name = "BOOLEAN"
        self.alignment = 4


# pylint: disable=too-few-public-methods
class Int16(Type):
    """
    AST representation of the D-Bus INT16 type.

    16-bit signed integer.
    """

    def __init__(self):
        """Constructor."""
        Type.__init__(self)
        self.type = "n"
        self.name = "INT16"
        self.alignment = 2


# pylint: disable=too-few-public-methods
class UInt16(Type):
    """
    AST representation of the D-Bus UINT16 type.

    16-bit unsigned integer.
    """

    def __init__(self):
        """Constructor."""
        Type.__init__(self)
        self.type = "q"
        self.name = "UINT16"
        self.alignment = 2


# pylint: disable=too-few-public-methods
class Int32(Type):
    """
    AST representation of the D-Bus INT32 type.

    32-bit signed integer.
    """

    def __init__(self):
        """Constructor."""
        Type.__init__(self)
        self.type = "i"
        self.name = "INT32"
        self.alignment = 4


# pylint: disable=too-few-public-methods
class UInt32(Type):
    """
    AST representation of the D-Bus UINT32 type.

    32-bit unsigned integer.
    """

    def __init__(self):
        """Constructor."""
        Type.__init__(self)
        self.type = "u"
        self.name = "UINT32"
        self.alignment = 4


# pylint: disable=too-few-public-methods
class Int64(Type):
    """
    AST representation of the D-Bus INT64 type.

    64-bit signed integer.
    """

    def __init__(self):
        """Constructor."""
        Type.__init__(self)
        self.type = "x"
        self.name = "INT64"
        self.alignment = 8


# pylint: disable=too-few-public-methods
class UInt64(Type):
    """
    AST representation of the D-Bus UINT64 type.

    64-bit unsigned integer.
    """

    def __init__(self):
        """Constructor."""
        Type.__init__(self)
        self.type = "t"
        self.name = "UINT64"
        self.alignment = 8


# pylint: disable=too-few-public-methods
class Double(Type):
    """
    AST representation of the D-Bus DOUBLE type.

    IEEE 754 double.
    """

    def __init__(self):
        """Constructor."""
        Type.__init__(self)
        self.type = "d"
        self.name = "DOUBLE"
        self.alignment = 8


# pylint: disable=too-few-public-methods
class String(Type):
    """
    AST representation of the D-Bus STRING type.

    UTF-8 string (must be valid UTF-8). Must be nul terminated and contain no
    other nul bytes.
    """

    def __init__(self):
        """Constructor."""
        Type.__init__(self)
        self.type = "s"
        self.name = "STRING"
        self.alignment = 4


# pylint: disable=too-few-public-methods
class ObjectPath(Type):
    """
    AST representation of the D-Bus OBJECT_PATH type.

    Name of an object instance.
    """

    def __init__(self):
        """Constructor."""
        Type.__init__(self)
        self.type = "o"
        self.name = "OBJECT_PATH"
        self.alignment = 4


# pylint: disable=too-few-public-methods
class Signature(Type):
    """
    AST representation of the D-Bus SIGNATURE type.
    """

    def __init__(self):
        """Constructor."""
        Type.__init__(self)
        self.type = "g"
        self.name = "SIGNATURE"
        self.alignment = 1


# pylint: disable=too-few-public-methods
class Variant(Type):
    """
    AST representation of the D-Bus VARIANT type.

    Variant type - the type of the value is part of the value itself.
    """

    def __init__(self):
        """Constructor."""
        Type.__init__(self)
        self.type = "v"
        self.name = "VARIANT"
        self.alignment = 1


# pylint: disable=too-few-public-methods
class UnixFD(Type):
    """
    AST representation of the D-Bus UNIX_FD type.

    Unix file descriptor.
    """

    def __init__(self):
        """Constructor."""
        Type.__init__(self)
        self.type = "h"
        self.name = "UNIX_FD"
        self.alignment = 4


# pylint: disable=too-few-public-methods
class Container(Type):
    """
    An abstract class - AST representation of the D-Bus container type.
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        """Constructor."""
        Type.__init__(self)
        self.members = []

    @abstractmethod
    def __str__(self):
        """Format the type as a human-readable string."""
        pass


# pylint: disable=too-few-public-methods
class Array(Container):
    """
    AST representation of the D-Bus ARRAY type.
    """

    def __init__(self):
        """Constructor."""
        Container.__init__(self)
        self.type = "a"
        self.name = "ARRAY"
        self.alignment = 4

    def __str__(self):
        """Format the type as a human-readable string."""
        assert len(self.members) == 1
        return "{}{}".format(self.type, self.members[0])


# pylint: disable=too-few-public-methods
class Struct(Container):
    """
    AST representation of the D-Bus STRUCT type.
    """

    def __init__(self):
        """Constructor."""
        Container.__init__(self)
        self.type = "r"
        self.name = "STRUCT"
        self.alignment = 8

    def __str__(self):
        """Format the type as a human-readable string."""
        return "({})".format("".join(map(str, self.members)))


# pylint: disable=too-few-public-methods
class DictEntry(Container):
    """
    AST representation of the D-Bus DICT_ENTRY type.
    """

    def __init__(self):
        """Constructor."""
        Container.__init__(self)
        self.type = "e"
        self.name = "DICT_ENTRY"
        self.alignment = 8

    def __str__(self):
        """Format the type as a human-readable string."""
        assert len(self.members) == 2
        return "{{{}{}}}".format(self.members[0], self.members[1])


# pylint: disable=too-few-public-methods
class TypeSignature(object):
    """
    AST representation of a D-Bus signature - an ordered list of one or more
    types.

    See http://dbus.freedesktop.org/doc/dbus-specification.html#type-system
    """

    def __init__(self):
        """Constructor."""
        self.members = []

    def __str__(self):
        """Format the type as a human-readable string."""
        return "".join(map(str, self.members))

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)
