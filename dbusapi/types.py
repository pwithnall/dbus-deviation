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


class Type(object):

    """
    An abstract class - AST representation of a D-Bus type.

    See http://dbus.freedesktop.org/doc/dbus-specification.html#type-system
    """

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


class Container(Type):

    """
    An abstract class - AST representation of the D-Bus container type.
    """

    def __init__(self):
        """Constructor."""
        Type.__init__(self)
        self.members = []

    def __str__(self):
        """Format the type as a human-readable string."""
        return "".join(map(str, self.members))


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
        member = str(self.members[0]) if len(self.members) > 0 else "?"
        return "{}{}".format(self.type, member)


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
        key = str(self.members[0]) if self.members > 0 else "?"
        val = str(self.members[1]) if self.members > 1 else "?"
        return "{{{}{}}}".format(key, val)


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
