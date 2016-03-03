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
Wrapper around dbus-interface-diff to integrate it with a VCS

This implements an API signature database in the project’s version control
system so that all users of the VCS can do API compatibility between all past
signed releases. Currently, only git is supported.

Requirements:
 • Support out-of-tree builds, where srcdir ≠ builddir.
 • Support bare repositories, or where GIT_WORK_TREE ≠ .git.
 • Exit with status 0 if GIT_DIR does not exist; support the use case of
   running `make distcheck` inside an extracted release tarball.
 • Support both tag-before-dist and tag-after-dist workflows.
"""

import argparse
from contextlib import contextmanager
import os
import pipes
import shlex
import shutil
import subprocess
import sys
import tempfile


@contextmanager
def named_pipe():
    """Create and cleanup a named pipe in a temporary directory."""
    dirname = tempfile.mkdtemp()
    try:
        path = os.path.join(dirname, 'fifo')
        os.mkfifo(path)
        yield path
    finally:
        shutil.rmtree(dirname)


def _git_command(args, command):
    """Build a git command line with standard arguments."""
    out = [args.git]
    if args.git_dir != '':
        out += ['--git-dir', args.git_dir]
    if args.git_work_tree != '':
        out += ['--work-tree', args.git_work_tree]

    return out + [command]


def _format_command(args):
    """Local wrapper for pipes.quote() with support for Python 2.7."""
    try:
        # pylint: disable=no-member
        return ' '.join(shlex.quote(a) for a in args)
    except AttributeError:
        try:
            # pylint: disable=no-member
            return ' '.join(pipes.quote(a) for a in args)
        except AttributeError:
            # Give up
            return ' '.join(args)


def _get_contents_of_file(args, tag, api_xml_file):
    """Get the git object ID of api_xml_file in the tag revision."""
    rev = subprocess.check_output(_git_command(args, 'rev-parse') +
                                  ['--verify', '--quiet',
                                   '%s^{tag}:%s' % (tag, api_xml_file)])
    return rev.strip().decode('utf-8')


def _set_notes_for_ref(args, tag, api_xml_basename, notes):
    """Store the notes object ID as api_xml_basename in the tag revision."""
    with open(os.devnull, 'w') as dev_null:
        subprocess.check_output(_git_command(args, 'notes') +
                                ['--ref',
                                 'refs/%s/%s' %
                                 (args.dbus_api_git_refs, api_xml_basename),
                                 'add', '-C', notes, tag],
                                stderr=dev_null)


def _notes_exist_for_ref(args, tag, api_xml_basename):
    """Check whether notes have already been stored for this file and tag."""
    with open(os.devnull, 'w') as dev_null:
        status = subprocess.call(_git_command(args, 'notes') +
                                 ['--ref',
                                  'refs/%s/%s' %
                                  (args.dbus_api_git_refs, api_xml_basename),
                                  'show', tag],
                                 stdout=dev_null,
                                 stderr=dev_null)
        return status == 0


def _get_notes_filename_for_head(args, api_xml_basename):
    """Get the filename of api_xml_basename in the git work tree."""
    filename = subprocess.check_output(_git_command(args, 'ls-files') +
                                       ['--full-name',
                                        '*/%s' % api_xml_basename])
    filename = filename.strip().decode('utf-8')

    # Resolve the relative path against the work tree.
    if args.git_work_tree != '':
        filename = os.path.join(args.git_work_tree, filename)

    return filename


def _fetch_notes(args):
    """Fetch the latest API signature database from the remote."""
    subprocess.check_output(_git_command(args, 'fetch') +
                            [args.git_remote_origin,
                             'refs/%s/*:refs/%s/*' %
                             (args.dbus_api_git_refs, args.dbus_api_git_refs)])


def _push_notes(args):
    """Push the local API signature database to the remote."""
    command = _git_command(args, 'push')
    command += [args.git_remote_origin,
                'refs/' + args.dbus_api_git_refs + '/*']

    if not args.no_push:
        subprocess.check_output(command)
    else:
        sys.stdout.write('Run this command to push the API signature '
                         'database:\n'
                         '   %s\n' % _format_command(command))


def _is_release(args, ref):
    """Check whether ref identifies a signed tag."""
    with open(os.devnull, 'w') as dev_null:
        code = subprocess.call(_git_command(args, 'rev-parse') +
                               ['--verify', ref],
                               stdout=dev_null, stderr=dev_null)
    return code == 0


def _get_latest_release(args):
    """Get the name of the latest signed tag."""
    tag_list = subprocess.check_output(_git_command(args, 'rev-list') +
                                       ['--tags', '--max-count=1'])
    tag_list = tag_list.strip().decode('utf-8').split('\n')
    latest_tag = subprocess.check_output(_git_command(args, 'describe') +
                                         ['--tags'] + tag_list)

    return latest_tag.strip().decode('utf-8')


def command_dist(args):
    """Store the current API signature against the latest signed tag."""
    # Get the latest git tag
    try:
        latest_tag = _get_latest_release(args)
    except subprocess.CalledProcessError:
        sys.stderr.write('error: Failed to find latest git tag: %s.')
        return 1

    # Store notes for each API file
    for api_xml_file in args.dbus_api_xml_files:
        try:
            api_xml_basename = os.path.basename(api_xml_file)

            # Do notes already exist for this file and tag?
            if args.ignore_existing and \
               _notes_exist_for_ref(args, latest_tag, api_xml_basename):
                sys.stdout.write('%s: Ignored XML file ‘%s’; already has '
                                 'a note\n' %
                                 (latest_tag, api_xml_basename))
                continue

            notes = _get_contents_of_file(args, latest_tag, api_xml_file)
            subprocess.check_output(_git_command(args, 'notes') +
                                    ['--ref',
                                     'refs/%s/%s' %
                                     (args.dbus_api_git_refs,
                                      api_xml_basename),
                                     'add', '-C', notes, latest_tag])

            sys.stdout.write('%s: Added note ‘%s’ for XML file ‘%s’\n' %
                             (latest_tag, notes, api_xml_basename))
        except subprocess.CalledProcessError:
            sys.stderr.write('error: Failed to store notes for API file '
                             '‘%s’ and git tag ‘%s’.\n' %
                             (api_xml_file, latest_tag))
            return 1

    # Push to the remote
    try:
        _push_notes(args)
    except subprocess.CalledProcessError:
        sys.stderr.write('error: Failed to push notes to remote ‘%s’.\n' %
                         args.git_remote_origin)
        return 1

    return 0


# pylint: disable=too-many-locals,too-many-branches,too-many-statements
def command_check(args):
    """
    Check for API differences between two tags.

    If old_ref is not specified, it defaults to the latest signed tag. If
    new_ref is not specified, it defaults to the git work tree.
    """
    if args.old_ref != '' and not _is_release(args, args.old_ref):
        sys.stderr.write('error: Invalid --old-ref ‘%s’\n' % args.old_ref)
        return 1

    if args.new_ref != '' and not _is_release(args, args.new_ref):
        sys.stderr.write('error: Invalid --new-ref ‘%s’\n' % args.new_ref)
        return 1

    try:
        _fetch_notes(args)
    except subprocess.CalledProcessError:
        # Continue anyway
        sys.stderr.write('error: Failed to fetch latest refs.\n')

    old_ref = args.old_ref
    new_ref = args.new_ref

    if old_ref == '':
        # Get the latest git tag
        try:
            old_ref = _get_latest_release(args)
        except subprocess.CalledProcessError:
            sys.stderr.write('error: Failed to find latest git tag.\n')
            return 1

    try:
        refs = subprocess.check_output(_git_command(args, 'for-each-ref') +
                                       ['--format=%(refname)',
                                        'refs/%s' % args.dbus_api_git_refs])
        refs = refs.strip().decode('utf-8').split('\n')
    except subprocess.CalledProcessError:
        sys.stderr.write('error: Failed to get ref list.\n')
        return 1

    retval = 0

    for note_ref in refs:
        api_xml_basename = os.path.basename(note_ref)

        if args.silent:
            sys.stdout.write(' DIFF      %s\n' % api_xml_basename)
        else:
            sys.stdout.write('Comparing %s\n' % api_xml_basename)

        with named_pipe() as old_pipe_path, named_pipe() as new_pipe_path:
            old_notes_filename = old_pipe_path

            if new_ref == '':
                new_notes_filename = \
                    _get_notes_filename_for_head(args, api_xml_basename)
            else:
                new_notes_filename = new_pipe_path

            diff_command = ['dbus-interface-diff',
                            '--warnings', args.warnings,
                            '--file-display-name', api_xml_basename]
            if args.fatal_warnings:
                diff_command += ['--fatal-warnings']
            diff_command += [old_notes_filename, new_notes_filename]
            old_notes_command = _git_command(args, 'notes') + [
                '--ref',
                'refs/%s/%s' % (args.dbus_api_git_refs, api_xml_basename),
                'show', old_ref,
            ]
            new_notes_command = _git_command(args, 'notes') + [
                '--ref',
                'refs/%s/%s' % (args.dbus_api_git_refs, api_xml_basename),
                'show', new_ref,
            ]

            diff_proc = subprocess.Popen(diff_command)

            with open(old_pipe_path, 'wb') as old_pipe, \
                    open(os.devnull, 'w') as dev_null:
                old_notes_proc = subprocess.Popen(old_notes_command,
                                                  stdout=old_pipe,
                                                  stderr=dev_null)

                if new_ref == '':
                    new_notes_proc = None

                    # Debug output. Roughly equivalent to `set -v`.
                    if not args.silent:
                        ls_files_command = _git_command(args, 'ls-files') + [
                            '--full-name',
                            '*/%s' % api_xml_basename,
                        ]

                        if args.git_work_tree != '':
                            git_work_tree = args.git_work_tree + '/'
                        else:
                            git_work_tree = ''

                        sys.stdout.write('%s \\\n'
                                         '   <(%s) \\\n'
                                         '   %s`%s`\n' %
                                         (_format_command(diff_command[:-2]),
                                          _format_command(old_notes_command),
                                          git_work_tree,
                                          _format_command(ls_files_command)))
                else:
                    with open(new_pipe_path, 'wb') as new_pipe:
                        new_notes_proc = subprocess.Popen(new_notes_command,
                                                          stdout=new_pipe,
                                                          stderr=dev_null)

                    # Debug output. Roughly equivalent to `set -v`.
                    if not args.silent:
                        sys.stdout.write('%s \\\n'
                                         '   <(%s) \\\n'
                                         '   <(%s)\n' %
                                         (_format_command(diff_command[:-2]),
                                          _format_command(old_notes_command),
                                          _format_command(new_notes_command)))

                old_notes_proc.communicate()
                old_notes_proc.wait()

                if new_notes_proc is not None:
                    new_notes_proc.wait()

            diff_proc.wait()

            # Output the status from the first failure
            if retval == 0 and diff_proc.returncode != 0:
                retval = diff_proc.returncode

    return retval


def command_install(args):
    """Set up the API signature database for all existing signed tags."""
    try:
        tag_list = subprocess.check_output(_git_command(args, 'tag'))
        tag_list = tag_list.strip().decode('utf-8').split('\n')
    except subprocess.CalledProcessError:
        sys.stderr.write('error: Failed to get tag list.\n')
        return 1

    for tag in tag_list:
        outputted = False

        for api_xml_file in args.dbus_api_xml_files:
            api_xml_basename = os.path.basename(api_xml_file)

            try:
                notes = _get_contents_of_file(args, tag, api_xml_file)
            except subprocess.CalledProcessError:
                # Ignore it.
                notes = ''

            if notes == '':
                continue

            try:
                _set_notes_for_ref(args, tag, api_xml_basename, notes)

                sys.stdout.write('%s: Added note ‘%s’ for XML file ‘%s’\n' %
                                 (tag, notes, api_xml_basename))
                outputted = True
            except subprocess.CalledProcessError:
                # Ignore it
                continue

        if not outputted:
            sys.stdout.write('%s: Nothing to do\n' % tag)

    # Push the new refs
    try:
        _push_notes(args)
    except subprocess.CalledProcessError:
        sys.stderr.write('error: Failed to push notes to remote ‘%s’.\n' %
                         args.git_remote_origin)
        return 1

    return 0


def main():
    """Main helper implementation."""
    # Parse command line arguments.
    parser = argparse.ArgumentParser(
        description='Comparing D-Bus interface definitions')

    # Common arguments
    parser.add_argument('--silent', action='store_const', const=True,
                        default=False,
                        help='Silence all non-error output')
    # pylint: disable=bad-continuation
    parser.add_argument('--git', type=str, default='git', metavar='COMMAND',
                        help='Path to the git command, including extra '
                             'arguments')
    parser.add_argument('--git-dir', type=str, default='', metavar='PATH',
                        help='Path to the git directory in the project '
                             'checkout')
    parser.add_argument('--git-work-tree', type=str, default='',
                        metavar='PATH',
                        help='Path to the git work tree for the project')
    parser.add_argument('--git-remote', dest='git_remote_origin', type=str,
                        default='origin', metavar='REMOTE',
                        help='git remote to push notes to')
    # pylint: disable=bad-continuation
    parser.add_argument('--git-refs', dest='dbus_api_git_refs', type=str,
                        default='notes/dbus/api', metavar='REF-PATH',
                        help='Path beneath refs/ where the git notes will be'
                             ' stored containing the API signatures database')
    parser.add_argument('--no-push', action='store_const', const=True,
                        default=False,
                        help='Disable automatic pushing the API signature '
                             'database to a remote repository')

    subparsers = parser.add_subparsers()

    # dist command
    parser_dist = subparsers.add_parser('dist')
    parser_dist.add_argument('dbus_api_xml_files', metavar='API-FILE',
                             type=str, nargs='+',
                             help='D-Bus API XML file to check')
    parser_dist.add_argument('--ignore-existing', action='store_const',
                             const=True, default=False,
                             help='Ignore existing API signatures rather than '
                                  'erroring')
    parser_dist.set_defaults(func=command_dist)

    # check command
    parser_check = subparsers.add_parser('check')
    parser_check.add_argument('--diff-warnings', dest='warnings', type=str,
                              default='all',
                              help='Comma-separated list of warnings to '
                                   'enable when running dbus-interface-diff')
    parser_check.add_argument('--fatal-warnings', action='store_const',
                              const=True, default=False,
                              help='Treat all warnings as fatal')
    # pylint: disable=bad-continuation
    parser_check.add_argument('old_ref', metavar='OLD-REF',
                              type=str, nargs='?', default='',
                              help='Old ref to compare; or empty for the '
                                   'latest signed tag')
    parser_check.add_argument('new_ref', metavar='NEW-REF',
                              type=str, nargs='?', default='',
                              help='New ref to compare; or empty for HEAD')
    parser_check.set_defaults(func=command_check)

    # install command
    parser_install = subparsers.add_parser('install')
    parser_install.add_argument('dbus_api_xml_files', metavar='API-FILE',
                                type=str, nargs='+',
                                help='D-Bus API XML file to install')
    parser_install.set_defaults(func=command_install)

    args = parser.parse_args()

    # Bail early if the .git directory does not exist, since that's our data
    # store.
    git_dir = args.git_dir
    if git_dir == '':
        git_dir = os.path.join(args.git_work_tree, '.git')
    if not os.path.isdir(git_dir):
        sys.stderr.write('error: Could not find git directory ‘%s’. '
                         'Skipping.\n' % git_dir)
        return 0

    return args.func(args)

if __name__ == '__main__':
    main()
