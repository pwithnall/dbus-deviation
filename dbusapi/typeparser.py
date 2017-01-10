# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
#
# Copyright © 2016 Kaloyan Tenchov
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
Module providing a `TypeParser` object for parsing D-Bus type strings into
abstract syntax trees (ASTs) representing the nested type structure.
"""


from dbusapi import types
from dbusapi.log import Log


class TypeParsingLog(Log):

    """Specialized Log subclass for type parsing messages"""

    def __init__(self):
        """Construct a new TypeParsingLog"""
        super(TypeParsingLog, self).__init__()
        self.register_issue_code('invalid-type')
        self.register_issue_code('reserved-type')
        self.register_issue_code('unknown-type')
        self.domain = 'types'


class TypeParser(object):

    """
    Parse and validate a D-Bus type string.

    The D-Bus type system and type strings are explained in detail in the
    D-Bus specification:
    https://dbus.freedesktop.org/doc/dbus-specification.html#type-system
    and in the GVariant documentation for GLib:
    https://developer.gnome.org/glib/stable/glib-GVariantType.html#id-1.6.18.6.9
    """

    def __init__(self, signature):
        """
        Construct a new TypeParser.

        Args:
            signature: a D-Bus type string
        """
        self.signature = signature
        self._log = TypeParsingLog()
        self._index = 0

    @staticmethod
    def get_output_codes():
        """Return a list of all possible output codes."""
        return TypeParsingLog().issue_codes

    def get_output(self):
        """Return a list of all logged parser messages."""
        return self._log.issues

    def _get_next_character(self):
        """Return the next character from the signature."""
        if self._index < len(self.signature):
            character = self.signature[self._index]
            self._index += 1
        else:
            character = None
        return character

    # pylint: disable=too-many-return-statements,too-many-branches
    def _parse_one_type(self, character):
        """Parse one complete type from the signature."""
        basic_types = {
            'y': types.Byte,
            'b': types.Boolean,
            'n': types.Int16,
            'q': types.UInt16,
            'i': types.Int32,
            'u': types.UInt32,
            'x': types.Int64,
            't': types.UInt64,
            'd': types.Double,
            's': types.String,
            'o': types.ObjectPath,
            'g': types.Signature,
            'v': types.Variant,
            'h': types.UnixFD,
        }

        if character in basic_types:
            return basic_types[character]()
        elif character == "a":
            out_array = types.Array()
            character = self._get_next_character()
            if not character:
                self._log.log_issue('invalid-type',
                                    'Incomplete array declaration.')
                return None
            one_type = self._parse_one_type(character)
            if not one_type:
                # Invalid member type - error has already been logged.
                return None
            out_array.members.append(one_type)
            return out_array
        elif character == "(":
            out_struct = types.Struct()
            while True:
                character = self._get_next_character()
                if not character or \
                   (character == ')' and len(out_struct.members) == 0):
                    self._log.log_issue('invalid-type',
                                        'Incomplete structure declaration.')
                    return None
                elif character == ")":
                    break
                one_type = self._parse_one_type(character)
                if not one_type:
                    # Invalid member type - error has already been logged.
                    return None
                out_struct.members.append(one_type)
            return out_struct
        elif character == "{":
            out_dict = types.DictEntry()
            while True:
                character = self._get_next_character()
                if not character or \
                   (character == '}' and len(out_dict.members) != 2):
                    self._log.log_issue('invalid-type',
                                        'Incomplete dictionary declaration.')
                    return None
                elif character == "}":
                    break
                one_type = self._parse_one_type(character)
                if not one_type:
                    # Invalid member type - error has already been logged.
                    return None
                if len(out_dict.members) >= 2:
                    self._log.log_issue('invalid-type',
                                        'Invalid dictionary declaration.')
                    return None
                out_dict.members.append(one_type)
            return out_dict
        elif character in ['r', 'e', 'm', '*', '?', '@', '&', '^']:
            # https://dbus.freedesktop.org/doc/dbus-specification.html#idm399
            self._log.log_issue('reserved-type',
                                'Reserved type ‘%s’ must not be used in '
                                'signatures on D-Bus.' % character)
            return None
        else:
            self._log.log_issue('unknown-type',
                                'Unknown type ‘%s’.' % character)
            return None

    def parse(self):
        """
        Parse the type string and build an AST of the type

        Returns:
            A non-empty list of types.

            If parsing fails, or if the input string is empty,
            None is returned.
        """
        self._log.clear()
        self._index = 0

        if len(self.signature) == 0:
            self._log.log_issue('invalid-type', 'Empty type string.')

        out = types.TypeSignature()
        while True:
            character = self._get_next_character()
            if not character:
                break

            one_type = self._parse_one_type(character)
            if not one_type:
                # Invalid type
                break

            out.members.append(one_type)

        if self._log.issues:
            return None

        return out
