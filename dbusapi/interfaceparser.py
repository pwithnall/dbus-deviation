# -*- coding: utf-8 -*-
#
# Copyright © 2015 Collabora Ltd.
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
Module providing an `InterfaceParser` object for parsing D-Bus introspection
XML files into abstract syntax trees (ASTs).
"""

# pylint: disable=no-member
from lxml import etree
from dbusapi.ast import AstLog, Node, TP_DTD


def _skip_non_node(elem):
    for node in elem.getchildren():
        if node.tag == 'node':
            return node

    return None


class ParsingLog(AstLog):

    """A specialized AstLog subclass for parsing issues"""

    def __init__(self, filename):
        """
        Construct a new ParsingLog.

        Args:
            filename: str, the name of the file being parsed.
        """
        super(ParsingLog, self).__init__()
        self.__filename = filename
        self.domain = 'parser'

    def _create_entry(self, code, message):
        return self.__filename, self.domain, code, message


class InterfaceParser(object):

    """
    Parse a D-Bus introspection XML file.

    This validates the file, but not exceedingly strictly. It is a pragmatic
    parser, designed for use by the InterfaceComparator rather than more
    general code. It ignores certain common extensions found in introspection
    XML files, such as documentation elements, but will fail on other
    unrecognised elements.
    """

    def __init__(self, filename):
        """
        Construct a new InterfaceParser.

        Args:
            filename: path to the XML introspection file to parse
        """
        self._filename = filename
        self._log = ParsingLog(filename)

    @staticmethod
    def get_output_codes():
        """Return a list of all possible output codes."""
        return ParsingLog(None).issue_codes

    def get_output(self):
        """Return a list of all logged parser messages."""
        return self._log.issues

    def _get_root(self):
        root = etree.parse(self._filename).getroot()

        # Handle specifications wrapped in tp:spec.
        if root.tag == '{%s}spec' % TP_DTD:
            root = _skip_non_node(root)

        if root is not None and root.tag != 'node':
            self._log.log_issue('unknown-node',
                                'Unknown root node ‘%s’.' % root.tag)
            root = _skip_non_node(root)

        return root

    def parse_with_nodes(self):
        """
        Parse the introspection XML file and build an AST.

        Returns:
            An ast.Node instance, representing the root node.
            If parsing fails, None is returned.
        """
        self._log.clear()

        root = self._get_root()
        if root is None:
            return None

        root_node = Node.from_xml(root, None, self._log)

        if root_node.name and \
           not Node.is_valid_absolute_object_path(root_node.name):
            self._log.log_issue('node-name',
                                'Root node name is not an absolute object '
                                'path ‘%s’.' % root_node.name)

        if self._log.issues:
            return None

        return root_node

    def parse(self):
        """
        Parse the introspection XML file and build an AST.

        Returns:
            A non-empty dict of interfaces belonging to the root node in the
            file, mapping each interface name to an ast.Interface instance.
            If parsing fails, None is returned.
        """
        root_node = self.parse_with_nodes()
        interfaces = root_node.interfaces if root_node else None

        return interfaces
