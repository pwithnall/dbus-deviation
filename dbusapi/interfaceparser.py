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

"""TODO"""

# pylint: disable=no-member
from lxml import etree
from dbusapi.ast import AstLog, Node, TP_DTD


def _skip_non_node(elem):
    for node in elem.getchildren():
        if node.tag == 'node':
            return node

    return None


def _get_root(filename, log):
    root = etree.parse(filename).getroot()

    # Handle specifications wrapped in tp:spec.
    if root.tag == '{%s}spec' % TP_DTD:
        root = _skip_non_node(root)

    if root is not None and root.tag != 'node':
        log.log_issue('unknown-node',
                      'Unknown root node ‘%s’.' % root.tag)
        root = _skip_non_node(root)

    return root


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
        self._output = []

    @staticmethod
    def get_output_codes():
        """Return a list of all possible output codes."""
        return ParsingLog(None).issue_codes

    def get_output(self):
        """Return a list of all logged parser messages."""
        return self._output

    def parse_with_nodes(self):
        """
        Parse the introspection XML file and build an AST.

        Returns:
            An ast.Node instance, representing the root node.
            If parsing fails, None is returned.
        """
        log = ParsingLog(self._filename)

        root = _get_root(self._filename, log)

        if root is None:
            self._output = log.issues
            return None

        root_node = Node.from_xml(root, None, log)

        if root_node.name and \
           not Node.is_valid_absolute_object_path(root_node.name):
            log.log_issue('node-name',
                          'Root node name is not an absolute object path '
                          '‘%s’.' % root_node.name)

        self._output = log.issues

        if self._output:
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
