#!/usr/bin/python
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
Parse D-Bus introspection XML and process it in various ways
"""

from setuptools import setup, find_packages
import os
import version  # https://gist.github.com/pwithnall/7bc5f320b3bdf418265a


project_name = 'dbus-deviation'
__version__ = version.get_version()
project_author = 'Philip Withnall'
README = open('README').read()
NEWS = open('NEWS').read()


# From http://stackoverflow.com/a/17004263/2931197
def discover_and_run_tests():
    import os
    import sys
    import unittest

    # get setup.py directory
    setup_file = sys.modules['__main__'].__file__
    setup_dir = os.path.abspath(os.path.dirname(setup_file))

    # use the default shared TestLoader instance
    test_loader = unittest.defaultTestLoader

    # use the basic test runner that outputs to sys.stderr
    test_runner = unittest.TextTestRunner()

    # automatically discover all tests
    # NOTE: only works for python 2.7 and later
    test_suite = test_loader.discover(setup_dir)

    # run the test suite
    test_runner.run(test_suite)

try:
    from setuptools.command.test import test

    class DiscoverTest(test):

        def finalize_options(self):
            test.finalize_options(self)
            self.test_args = []
            self.test_suite = True

        def run_tests(self):
            discover_and_run_tests()

except ImportError:
    from distutils.core import Command

    class DiscoverTest(Command):
        user_options = []

        def initialize_options(self):
                pass

        def finalize_options(self):
            pass

        def run(self):
            discover_and_run_tests()


setup(
    name=project_name,
    version=__version__,
    packages=find_packages(exclude=['*.tests']),
    include_package_data=True,
    exclude_package_data={'': ['.gitignore']},
    zip_safe=True,
    setup_requires=[
        'setuptools_git >= 0.3',
        'setuptools_pep8',
        'sphinx',
    ],
    install_requires=['lxml'],
    tests_require=[],
    entry_points={
        'console_scripts': [
            'dbus-interface-diff = dbusdeviation.utilities.diff:main',
            'dbus-interface-vcs-helper = '
            'dbusdeviation.utilities.vcs_helper:main',
        ],
    },
    author=project_author,
    author_email='philip.withnall@collabora.co.uk',
    description=__doc__,
    long_description=README + '\n\n' + NEWS,
    license='LGPLv2.1+',
    url='http://people.collabora.com/~pwith/dbus-deviation/',
    cmdclass={'test': DiscoverTest},
    command_options={
        'build_sphinx': {
            'project': ('setup.py', project_name),
            'version': ('setup.py', __version__),
            'release': ('setup.py', __version__),
        },
    },
)
