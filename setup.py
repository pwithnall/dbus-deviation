#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

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
