#!/usr/bin/python
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

"""
Parse D-Bus introspection XML and process it in various ways
"""

from setuptools import setup, find_packages
import os


__version__ = '0.1.0'
README = open('README').read()
NEWS = open('NEWS').read()


setup(
    name='dbus-deviation',
    version=__version__,
    packages=find_packages(exclude=['*.tests']),
    include_package_data=True,
    exclude_package_data={'': ['.gitignore']},
    zip_safe=True,
    setup_requires=[
        'setuptools_git >= 0.3',
        'setuptools_pep8',
    ],
    install_requires=[],
    tests_require=[],
    entry_points={
        'console_scripts': [
            'dbus-interface-diff = dbusdeviation.utilities.diff:main',
        ],
    },
    author='Philip Withnall',
    author_email='philip.withnall@collabora.co.uk',
    description=__doc__,
    long_description=README + '\n\n' + NEWS,
    license='GPLv2+',
    url='http://people.collabora.com/~pwith/dbus-deviation/',
    test_suite='dbusdeviation.tests',
)
