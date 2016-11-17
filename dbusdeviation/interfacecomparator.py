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
Module providing a `InterfaceComparator` object for comparing two D-Bus APIs
(provided as abstract syntax trees from the introspection XML), to determine if
they differ in API-incompatible ways.
"""

from dbusapi import ast


# Warning categories.
WARNING_CATEGORIES = [
    'info',
    'backwards-compatibility',
    'forwards-compatibility',
]


class InterfaceComparator(object):

    """
    Compare two D-Bus interface descriptions and determine how they differ.

    Differences are given different severity levels, depending on whether they
    affect

    * nothing, and are purely decorative; for example, changing the name of a
      method argument
    * forwards compatibility, where code written against the new interface
      may not work against the old interface; for example, because it uses a
      newly added method
    * backwards compatibility, where code written against the old interface
      may not work against the new interface; for example, because it changes
      the type of a property
    """

    # Output severity levels.
    OUTPUT_INFO = 'info'
    OUTPUT_FORWARDS_INCOMPATIBLE = 'forwards-compatibility'
    OUTPUT_BACKWARDS_INCOMPATIBLE = 'backwards-compatibility'

    def __init__(self, old_interfaces, new_interfaces,
                 enabled_warnings=None, disabled_warnings=None,
                 new_filename=None):
        """
        Construct a new InterfaceComparator.

        Args:
            old_interfaces: non-empty dict of old interfaces, mapping
                interface name to an ast.Interface instance
            new_interfaces: non-empty dict of new interfaces, mapping
                interface name to an ast.Interface instance
            enabled_warnings: potentially empty list of warning categories and
                codes to enable
            disabled_warnings: potentially empty list of warning categories and
                codes to disable
            new_filename: path to the new D-Bus interface file,
                or None if unknown
        """
        self._old_interfaces = old_interfaces
        self._new_interfaces = new_interfaces
        self._new_filename = new_filename
        self._output = []

        if enabled_warnings is not None:
            self._enabled_warnings = enabled_warnings
        else:
            self._enabled_warnings = WARNING_CATEGORIES

        if disabled_warnings is not None:
            self._disabled_warnings = disabled_warnings
        else:
            self._disabled_warnings = []

    @staticmethod
    def get_output_codes():
        """Return a list of all possible output codes."""
        # FIXME: Hard-coded for the moment.
        return [
            'interface-added',
            'interface-removed',
            'deprecated',
            'undeprecated'
            'c-symbol-changed',
            'reply-added',
            'reply-removed',
            'ecs-changed-true-invalidates',
            'ecs-changed-true-false',
            'ecs-changed-true-const',
            'ecs-changed-invalidates-true',
            'ecs-changed-invalidates-false',
            'ecs-changed-invalidates-const',
            'ecs-changed-false-invalidates',
            'ecs-changed-false-true',
            'ecs-changed-false-const',
            'ecs-changed-const-invalidates',
            'ecs-changed-const-true',
            'ecs-changed-const-false',
            'method-added',
            'method-removed',
            'property-added',
            'property-removed',
            'signal-added',
            'signal-removed',
            'argument-added',
            'argument-removed',
            'property-type-changed',
            'property-access-changed-read-readwrite',
            'property-access-changed-read-write',
            'property-access-changed-write-read',
            'property-access-changed-write-readwrite',
            'property-access-changed-readwrite-read',
            'property-access-changed-readwrite-write',
            'argument-name-changed',
            'argument-type-changed',
            'argument-direction-changed-in-out',
            'argument-direction-changed-out-in',
        ]

    def _issue_output(self, level, code, message):
        """Append a message to the comparator output."""
        self._output.append((self._new_filename, level, code, message))

    def _warning_enabled(self, level, code):
        """Determine whether the given output level is enabled for output."""
        return ((level in self._enabled_warnings and
                 level not in self._disabled_warnings and
                 code not in self._disabled_warnings) or
                (code in self._enabled_warnings and
                 code not in self._disabled_warnings))

    def get_output(self):
        """
        Return all the log messages generated by the latest call to compare().

        Disabled warnings will not be returned.
        """
        out = []

        for (filename, level, code, message) in self._output:
            if not self._warning_enabled(level, code):
                continue

            out.append((filename, level, code, message))

        return out

    def compare(self):
        """
        Compare the two interfaces and store the results.

        Returns:
            The list of relevant warnings to output; an empty list otherwise.
            The return value is affected by the categories of enabled
            warnings.
        """
        self._output = []

        for (name, interface) in self._old_interfaces.items():
            # See if the old interface exists in the new file.
            if name not in self._new_interfaces:
                self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                                   'interface-removed',
                                   'Interface ‘%s’ has been removed.' % name)
            else:
                # Compare the two.
                self._compare_interfaces(interface, self._new_interfaces[name])

        for (name, interface) in self._new_interfaces.items():
            # See if the new interface exists in the old file.
            if name not in self._old_interfaces:
                self._issue_output(self.OUTPUT_FORWARDS_INCOMPATIBLE,
                                   'interface-added',
                                   'Interface ‘%s’ has been added.' % name)

        # Work out the exit status.
        return self.get_output()

    # pylint: disable=too-many-branches
    def _compare_annotations(self, old_node, new_node):  # noqa
        """Compare two ast.Annotation instances."""

        def _get_string_annotation(node, annotation_name, default):
            """
            Get an annotation value as a string.

            Reference: http://goo.gl/3EtdNf

            Returns:
                The value of the `annotation_name` annotation as a string, or
                `default` if no annotation exists by that name.
            """
            if annotation_name in node.annotations:
                return node.annotations[annotation_name].value
            return default

        def _get_bool_annotation(node, annotation_name, default):
            """
            Get an annotation value as a boolean.

            Reference: http://goo.gl/3EtdNf

            Returns:
                The value of the `annotation_name` annotation as a boolean, or
                `default` if no annotation exists by that name.
            """
            if annotation_name in node.annotations:
                return node.annotations[annotation_name].value == 'true'
            return default

        def _get_ecs_annotation(node):
            """
            Get the value of the EmitsChangedSignal annotation.

            Reference: http://goo.gl/3EtdNf

            Returns:
                The value of the
                `org.freedesktop.DBus.Property.EmitsChangedSignal` annotation,
                if it exists, or the default, calculated as per the
                specification.
            """
            name = 'org.freedesktop.DBus.Property.EmitsChangedSignal'

            if name in node.annotations:
                return node.annotations[name].value
            elif isinstance(node, ast.Property):
                assert node.interface is not None
                return _get_ecs_annotation(node.interface)
            else:
                return 'true'

        old_deprecated = \
            _get_bool_annotation(old_node,
                                 'org.freedesktop.DBus.Deprecated', False)
        new_deprecated = \
            _get_bool_annotation(new_node,
                                 'org.freedesktop.DBus.Deprecated', False)

        if old_deprecated and not new_deprecated:
            self._issue_output(self.OUTPUT_INFO, 'undeprecated',
                               'Node ‘%s’ has been un-deprecated.' %
                               old_node.format_name())
        elif not old_deprecated and new_deprecated:
            self._issue_output(self.OUTPUT_INFO, 'deprecated',
                               'Node ‘%s’ has been deprecated.' %
                               old_node.format_name())

        old_c_symbol = \
            _get_string_annotation(old_node,
                                   'org.freedesktop.DBus.GLib.CSymbol', '')
        new_c_symbol = \
            _get_string_annotation(new_node,
                                   'org.freedesktop.DBus.GLib.CSymbol', '')

        if old_c_symbol != new_c_symbol:
            self._issue_output(self.OUTPUT_INFO, 'c-symbol-changed',
                               'Node ‘%s’ has changed its C symbol from ‘%s’ '
                               'to ‘%s’.' %
                               (old_node.format_name(), old_c_symbol,
                                new_c_symbol))

        old_no_reply = \
            _get_bool_annotation(old_node,
                                 'org.freedesktop.DBus.Method.NoReply', False)
        new_no_reply = \
            _get_bool_annotation(new_node,
                                 'org.freedesktop.DBus.Method.NoReply', False)

        if old_no_reply and not new_no_reply:
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                               'reply-added',
                               'Node ‘%s’ has been marked as returning a '
                               'reply.' % old_node.format_name())
        elif not old_no_reply and new_no_reply:
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                               'reply-removed',
                               'Node ‘%s’ has been marked as not returning a '
                               'reply.' % old_node.format_name())

        old_ecs = _get_ecs_annotation(old_node)
        new_ecs = _get_ecs_annotation(new_node)
        output_code = 'ecs-changed-%s-%s' % (old_ecs, new_ecs)

        #                                 New
        #                   | true | invalidates | const | false
        #     | true        | xxxx | B2          | F3    | F3
        # Old | invalidates | B2   | xxxxxxxxxxx | F3    | F3
        #     | const       | B1   | B1          | xxxxx | B4
        #     | false       | B1   | B1          | F4    | xxxxx
        #
        # B = Backwards-compatible; F = Forwards-compatible
        # 1 = Started notifying
        # 2 = Property switched lists in PropertiesChanged
        # 3 = Stopped notifying
        # 4 = const semantics changed

        if old_ecs in ['true', 'invalidates'] and \
           new_ecs in ['false', 'const']:
            self._issue_output(self.OUTPUT_FORWARDS_INCOMPATIBLE, output_code,
                               'Node ‘%s’ stopped emitting '
                               'org.freedesktop.DBus.Properties.'
                               'PropertiesChanged.' %
                               old_node.format_name())
        elif (old_ecs in ['false', 'const'] and
              new_ecs in ['true', 'invalidates']):
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE, output_code,
                               'Node ‘%s’ started emitting '
                               'org.freedesktop.DBus.Properties.'
                               'PropertiesChanged.' %
                               old_node.format_name())
        elif old_ecs == 'true' and new_ecs == 'invalidates':
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE, output_code,
                               'Node ‘%s’ stopped emitting its new value in '
                               'org.freedesktop.DBus.Properties.'
                               'PropertiesChanged.' %
                               old_node.format_name())
        elif old_ecs == 'invalidates' and new_ecs == 'true':
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE, output_code,
                               'Node ‘%s’ started emitting its new value in '
                               'org.freedesktop.DBus.Properties.'
                               'PropertiesChanged.' %
                               old_node.format_name())
        elif old_ecs == 'const' and new_ecs == 'false':
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE, output_code,
                               'Node ‘%s’ stopped being a constant.' %
                               old_node.format_name())
        elif old_ecs == 'false' and new_ecs == 'const':
            self._issue_output(self.OUTPUT_FORWARDS_INCOMPATIBLE, output_code,
                               'Node ‘%s’ became a constant.' %
                               old_node.format_name())

    # pylint: disable=too-many-branches
    def _compare_interfaces(self, old_interface, new_interface):  # noqa
        """Compare two ast.Interface instances."""
        # Precondition of calling this method.
        assert old_interface.name == new_interface.name

        # Compare methods.
        for (name, method) in old_interface.methods.items():
            if name not in new_interface.methods:
                self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                                   'method-removed',
                                   'Method ‘%s’ has been removed.' %
                                   method.format_name())
            else:
                self._compare_methods(method, new_interface.methods[name])

        for (name, method) in new_interface.methods.items():
            if name not in old_interface.methods:
                self._issue_output(self.OUTPUT_FORWARDS_INCOMPATIBLE,
                                   'method-added',
                                   'Method ‘%s’ has been added.' %
                                   method.format_name())

        # Compare properties
        for (name, prop) in old_interface.properties.items():
            if name not in new_interface.properties:
                self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                                   'property-removed',
                                   'Property ‘%s’ has been removed.' %
                                   prop.format_name())
            else:
                self._compare_properties(prop, new_interface.properties[name])

        for (name, prop) in new_interface.properties.items():
            if name not in old_interface.properties:
                self._issue_output(self.OUTPUT_FORWARDS_INCOMPATIBLE,
                                   'property-added',
                                   'Property ‘%s’ has been added.' %
                                   prop.format_name())

        # Compare signals
        for (name, signal) in old_interface.signals.items():
            if name not in new_interface.signals:
                self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                                   'signal-removed',
                                   'Signal ‘%s’ has been removed.' %
                                   signal.format_name())
            else:
                self._compare_signals(signal,
                                      new_interface.signals[name])

        for (name, signal) in new_interface.signals.items():
            if name not in old_interface.signals:
                self._issue_output(self.OUTPUT_FORWARDS_INCOMPATIBLE,
                                   'signal-added',
                                   'Signal ‘%s’ has been added.' %
                                   signal.format_name())

        # Compare annotations
        self._compare_annotations(old_interface, new_interface)

    def _compare_methods(self, old_method, new_method):
        """Compare two ast.Method instances."""
        # Precondition of calling this method.
        assert old_method.name == new_method.name

        # Compare the argument lists.
        n_old_args = len(old_method.arguments)
        n_new_args = len(new_method.arguments)

        for i in range(max(n_old_args, n_new_args)):
            if i >= n_old_args:
                self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                                   'argument-added',
                                   'Argument %s '
                                   'has been added.' %
                                   new_method.arguments[i].format_name())
            elif i >= n_new_args:
                self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                                   'argument-removed',
                                   'Argument %s '
                                   'has been removed.' %
                                   old_method.arguments[i].format_name())
            else:
                self._compare_arguments(old_method.arguments[i],
                                        new_method.arguments[i])

        # Compare annotations
        self._compare_annotations(old_method, new_method)

    def _compare_properties(self, old_property, new_property):
        """Compare two ast.Property instances."""
        # Precondition of calling this method.
        assert old_property.name == new_property.name

        if old_property.type != new_property.type:
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                               'property-type-changed',
                               'Property ‘%s’ has changed type from ‘%s’ '
                               'to ‘%s’.' %
                               (old_property.format_name(),
                                old_property.type, new_property.type))

        error_code = 'property-access-changed-%s-%s' % \
                     (old_property.access, new_property.access)

        if (old_property.access == ast.Property.ACCESS_READ or
            old_property.access == ast.Property.ACCESS_WRITE) and \
           new_property.access == ast.Property.ACCESS_READWRITE:
            # Property has become less restrictive.
            self._issue_output(self.OUTPUT_FORWARDS_INCOMPATIBLE, error_code,
                               'Property ‘%s’ has changed access from '
                               '‘%s’ to ‘%s’, becoming less restrictive.' %
                               (old_property.format_name(),
                                old_property.access, new_property.access))
        elif old_property.access != new_property.access:
            # Access has changed incompatibly.
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE, error_code,
                               'Property ‘%s’ has changed access from '
                               '‘%s’ to ‘%s’.' %
                               (old_property.format_name(),
                                old_property.access, new_property.access))

        # Compare annotations
        self._compare_annotations(old_property, new_property)

    def _compare_signals(self, old_signal, new_signal):
        """Compare two ast.Signal instances."""
        # Precondition of calling this method.
        assert old_signal.name == new_signal.name

        # Compare the argument lists.
        n_old_args = len(old_signal.arguments)
        n_new_args = len(new_signal.arguments)

        for i in range(max(n_old_args, n_new_args)):
            if i >= n_old_args:
                self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                                   'argument-added',
                                   'Argument %s '
                                   'has been added.' %
                                   new_signal.arguments[i].format_name())
            elif i >= n_new_args:
                self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                                   'argument-removed',
                                   'Argument %s '
                                   'has been removed.' %
                                   old_signal.arguments[i].format_name())
            else:
                self._compare_arguments(old_signal.arguments[i],
                                        new_signal.arguments[i])

        # Compare annotations
        self._compare_annotations(old_signal, new_signal)

    def _compare_arguments(self, old_arg, new_arg):
        """Compare two ast.Argument instances."""
        if old_arg.name != new_arg.name:
            self._issue_output(self.OUTPUT_INFO,
                               'argument-name-changed',
                               'Argument %s has changed '
                               'name from ‘%s’ to ‘%s’.' %
                               (old_arg.pretty_name,
                                old_arg.name, new_arg.name))

        if old_arg.type != new_arg.type:
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                               'argument-type-changed',
                               'Argument %s has changed '
                               'type from ‘%s’ to ‘%s’.' %
                               (old_arg.pretty_name,
                                old_arg.type, new_arg.type))

        if old_arg.direction != new_arg.direction:
            self._issue_output(self.OUTPUT_BACKWARDS_INCOMPATIBLE,
                               'argument-direction-changed-%s-%s' %
                               (old_arg.direction, new_arg.direction),
                               'Argument %s has changed '
                               'direction from ‘%s’ to ‘%s’.' %
                               (old_arg.pretty_name,
                                old_arg.direction, new_arg.direction))

        # Compare annotations
        self._compare_annotations(old_arg, new_arg)
