# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
#
# Copyright © 2017 Philip Withnall
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
Module providing a `BasicTypeFormatter` object for formatting D-Bus type
abstract syntax trees (ASTs) into human-readable strings describing the type
structure.

These strings are intended to be easy to read for a technical reader, but
without having to memorise the single-character D-Bus types. They could be used
in documentation, for example.

Other type formatters may be added in future which format the type ASTs
differently.
"""


from dbusapi import types


class BasicTypeFormatter(object):
    """
    Format a D-Bus type AST as a string.

    Given a valid D-Bus type structure (see types.Type and
    types.TypeSignature), format it as a human-readable string. The format
    mirrors that used by D-Feet when introspecting D-Bus interfaces.

    In future, support may be added to this class for choosing the output
    language for the formatted strings.
    """

    def format(self, type_instance):
        """
        Format the type instance as a human-readable string.

        Note that the type instance must be a valid type structure. For
        example, this means that any types.Struct instance must have one or
        more child members; any types.DictEntry instance must have exactly two
        child members (key and value) and be the immediate child of a
        types.Array instance.

        See the D-Bus documentation for the full details of type system
        restrictions:
        https://dbus.freedesktop.org/doc/dbus-specification.html#type-system

        The type instance may be a types.Type instance or a types.TypeSignature
        instance.

        Args:
            type_instance: valid types.Type or types.TypeSignature instance
        """
        basic_type_map = {
            types.Byte: 'Byte',
            types.Boolean: 'Boolean',
            types.Int16: 'Int16',
            types.UInt16: 'UInt16',
            types.Int32: 'Int32',
            types.UInt32: 'UInt32',
            types.Int64: 'Int64',
            types.UInt64: 'UInt64',
            types.Double: 'Double',
            types.String: 'String',
            types.ObjectPath: 'Object Path',
            types.Signature: 'Signature',
            types.Variant: 'Variant',
            types.UnixFD: 'Unix FD',
        }

        # pylint: disable=unidiomatic-typecheck
        if isinstance(type_instance, types.TypeSignature):
            return ', '.join(map(self.format, type_instance.members))
        elif (isinstance(type_instance, types.Array) and
              isinstance(type_instance.members[0], types.DictEntry)):
            dictionary = type_instance.members[0]
            key = self.format(dictionary.members[0])
            value = self.format(dictionary.members[1])
            return 'Dict of {{{}: {}}}'.format(key, value)
        elif isinstance(type_instance, types.Array):
            member = self.format(type_instance.members[0])
            return 'Array of [{}]'.format(member)
        elif isinstance(type_instance, types.Struct):
            members = map(self.format, type_instance.members)
            return 'Struct of ({})'.format(', '.join(members))
        elif type(type_instance) in basic_type_map:
            return basic_type_map[type(type_instance)]
        else:
            assert False
