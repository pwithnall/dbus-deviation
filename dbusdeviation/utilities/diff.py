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
D-Bus interface comparator. This allows two D-Bus introspection XML files to be
compared for API compatibility, and any incompatibilities debugged.

Compatibility warnings are split into categories, separating forwards- and
backwards-compatibility in case one or other is not cared about by the
interface maintainer. See the documentation for InterfaceComparator for an
explanation of the two types of compatibility.
"""

import argparse
import sys

# PyPy support
try:
    from xml.etree import cElementTree as ElementTree
except ImportError:
    from xml.etree import ElementTree

from dbusapi.interfaceparser import InterfaceParser
from dbusdeviation.interfacecomparator import InterfaceComparator

# Warning categories.
WARNING_CATEGORIES = [
    'info',
    'backwards-compatibility',
    'forwards-compatibility',
]


def main():
    # Parse command line arguments.
    parser = argparse.ArgumentParser(
        description='Comparing D-Bus interface definitions')
    parser.add_argument('old_file', type=str, help='Old interface XML file')
    parser.add_argument('new_file', type=str, help='New interface XML file')
    parser.add_argument('--warnings', dest='warnings', metavar='CATEGORY,…',
                        type=str,
                        help='Warning categories (%s)' %
                             ', '.join(WARNING_CATEGORIES))

    args = parser.parse_args()

    if not args.old_file or not args.new_file:
        parser.print_help()
        sys.exit(1)

    if args.warnings is None:
        # Enable all warnings by default
        enabled_warnings = WARNING_CATEGORIES
    else:
        enabled_warnings = args.warnings.split(',')

    for category in enabled_warnings:
        if category not in WARNING_CATEGORIES:
            parser.print_help()
            sys.exit(1)

    # Parse the two files.
    old_parser = InterfaceParser(args.old_file)
    new_parser = InterfaceParser(args.new_file)

    try:
        old_interfaces = old_parser.parse()
    except ElementTree.ParseError as e:
        sys.stderr.write('Error parsing ‘%s’: %s\n' % (args.old_file, e))
        sys.exit(1)
    try:
        new_interfaces = new_parser.parse()
    except ElementTree.ParseError as e:
        sys.stderr.write('Error parsing ‘%s’: %s\n' % (args.new_file, e))
        sys.exit(1)

    # Handle errors
    if old_interfaces is None:
        sys.stderr.write('Error parsing ‘%s’:\n' % args.old_file)
        old_parser.print_output()
        sys.exit(1)
    if new_interfaces is None:
        sys.stderr.write('Error parsing ‘%s’:\n' % args.new_file)
        new_parser.print_output()
        sys.exit(1)

    # Compare the interfaces.
    comparator = InterfaceComparator(old_interfaces, new_interfaces,
                                     enabled_warnings)
    out = comparator.compare()
    comparator.print_output()
    sys.exit(len(out))

if __name__ == '__main__':
    main()
