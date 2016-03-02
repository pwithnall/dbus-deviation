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

# This Makefile can be included in the top-level Makefile.am in a project to
# provide rules for checking the API compatibility of D-Bus interface between
# different tagged releases of a project.
#
# To add it to your project, copy this file into your project, add it to git,
# and add the following lines to your top-level Makefile.am:
#
#    dbus_api_xml_files = list of D-Bus interface XML files
#    dbus_api_checkflags = --fatal-warnings
#    -include $(top_srcdir)/dbus-deviation.mk
#
# Do not list this file in EXTRA_DIST or similar — it is designed to be used
# from git checkouts only. Further configuration options are documented below.
#
# Then, run the following command to initialise the database of past versions
# of the XML files:
#
#    make dbus-deviation-mk-install
#
# It is safe to run this command multiple times, though there is no need to.
# It will not make changes to your remote repository, but will give you a
# `git push` command to run to push the database to a remote.
#
# Finally, copy pre-push.hook to .git/hooks/pre-push and ensure it’s
# executable. This script will automatically update the API signature database
# when a new release tag is pushed to the git remote. It is required for dist
# to succeed.
#
# If your project builds D-Bus interfaces at runtime, rather than automatically
# generating the code for them from XML files, you must populate the database
# manually. For each tagged release, and for each D-Bus interface, run:
#
#    xml_file=path/to/generated-api-description.xml
#    tag=release_tag_name
#    dbus_api_git_refs=notes/dbus/api  # matches the Makefile config
#    git_remote_origin=origin  # matches the Makefile config
#
#    git checkout "$tag"
#    # Build your program.
#    # Run your program.
#    # Call the org.freedesktop.DBus.Introspectable.Introspect() method.
#    # Save its output to $xml_file.
#
#    notes=$(git hash-object -w "$xml_file")
#    xml_basename=$(basename "$xml_file")
#    git notes --ref "refs/$(dbus_api_git_refs)/$xml_basename" \
#       add -C "$notes" "$tag"
#    git push "$(git_remote_origin)" refs/$(dbus_api_git_refs)/*
#
# The following configuration variables are mandatory:
#
#    dbus_api_xml_files:
#       Space-separated list of paths to the API XML files.
#
# The following are optional:
#
#    git_remote_origin (default: origin):
#       Remote to push/pull the API signature database to/from.
#    dbus_api_diff_warnings (default: all):
#       Comma-separated list of warnings to enable when running
#       dbus-interface-diff.
#    dbus_api_checkflags (default: empty):
#       Flags to pass to the ‘check’ operation of dbus-interface-vcs-helper.
#       Typically, this should be --fatal-warnings.
#    dbus_api_distflags (default: empty):
#       Flags to pass to the ‘dist’ operation of dbus-interface-vcs-helper.
#    dbus_api_git_refs (default: notes/dbus/api):
#       Path beneath refs/ where the git notes will be stored containing the
#       API signatures database.
#    GIT (default: git):
#       Path of the git program to run, including any custom arguments to
#       pass to every invocation of git.
#
# The Makefile hooks in to dist-hook and check-local to update the API
# signature database and to check for differences between the most recent
# release and the current working tree.
#
# This file support out-of-tree builds, and git repositories with non-standard
# GIT_WORK_TREE or GIT_DIR settings (bare repositories).

# Mandatory configuration.
dbus_api_xml_files ?=

# Optional configuration.
git_remote_origin ?= origin
dbus_api_diff_warnings ?= info,forwards-compatibility,backwards-compatibility
dbus_api_checkflags ?=
dbus_api_distflags ?=
dbus_api_git_refs ?= notes/dbus/api
dbus_api_git_work_tree ?= $(top_srcdir)
dbus_api_git_dir ?= $(dbus_api_git_work_tree)/.git
GIT = git

# Silent rules for dbus-interface-vcs-helper
dbus_interface_vcs_helper_v = $(dbus_interface_vcs_helper_v_$(V))
dbus_interface_vcs_helper_v_ = $(dbus_interface_vcs_helper_v_$(AM_DEFAULT_VERBOSITY))
dbus_interface_vcs_helper_v_0 = --silent
dbus_interface_vcs_helper_v_1 =

V_api = $(v_api_$(V))
v_api_ = $(v_api_$(AM_DEFAULT_VERBOSITY))
v_api_0 = @echo "  API     " $@;
v_api_1 =


# For each XML file in $(dbus_api_xml_files), add it to the API signature
# database for the most recent git tag.
dist-dbus-api-compatibility:
	$(V_api)dbus-interface-vcs-helper $(dbus_interface_vcs_helper_v) \
		--git "$(GIT)" \
		--git-dir "$(dbus_api_git_dir)" \
		--git-work-tree "$(dbus_api_git_work_tree)" \
		--git-refs "$(dbus_api_git_refs)" \
		--git-remote "$(git_remote_origin)" \
		dist --ignore-existing $(dbus_api_distflags) \
		$(dbus_api_xml_files)

# Check the pre-push hook is installed, otherwise the API signature database
# will not get pushed to the remote after the release tag is created.
dist-dbus-api-compatibility-check-hook:
	@if [ ! -x "$(dbus_api_git_dir)/hooks/pre-push" ] || \
	    ! grep dbus-interface-vcs-helper "$(dbus_api_git_dir)/hooks/pre-push"; then \
		echo "error: dbus-deviation git hook is not installed. Copy pre-push.hook to" 1>&2; \
		echo "          $(dbus_api_git_dir)/hooks/pre-push" 1>&2; \
		echo "       to enable updates to the D-Bus API signature database." 1>&2; \
		echo "       See dbus-deviation.mk for more details." 1>&2; \
		echo "Aborting." 1>&2; \
		exit 1; \
	fi

dist-hook: dist-dbus-api-compatibility dist-dbus-api-compatibility-check-hook
.PHONY: dist-dbus-api-compatibility dist-dbus-api-compatibility-check-hook


# Check that the D-Bus API signatures for the two refs given as OLD_REF and
# NEW_REF are compatible; error if they are not. The refs should typically be
# tags, specified as ‘tag_name^{tag}’, since the API signature database is not
# stored for non-tag refs by default.
#
# OLD_REF defaults to the most recent git tag. NEW_REF defaults to the current
# working tree — so running this rule with neither specified will check the
# current working tree against the latest release. If this happens during
# distcheck, it effectively checks the release-in-progress against the
# previous release, which is exactly what is expected of distcheck.
#
# If this is run on a source directory where $(dbus_api_git_dir) does not
# exist, it will print a message and exit successfully. This supports the use
# case where `make distcheck` is run on an extracted tarball of a release.
check-dbus-api-compatibility:
	$(V_api)dbus-interface-vcs-helper $(dbus_interface_vcs_helper_v) \
		--git "$(GIT)" \
		--git-dir "$(dbus_api_git_dir)" \
		--git-work-tree "$(dbus_api_git_work_tree)" \
		--git-refs "$(dbus_api_git_refs)" \
		--git-remote "$(git_remote_origin)" \
		check \
		--diff-warnings "$(dbus_api_diff_warnings)" \
		$(dbus_api_checkflags) \
		"$(OLD_REF)" "$(NEW_REF)"
check-local: check-dbus-api-compatibility
.PHONY: check-dbus-api-compatibility


# Installation rule to set up an API signature database for each existing tag.
# It is safe to run this multiple times.
dbus-deviation-mk-install:
	$(V_api)dbus-interface-vcs-helper $(dbus_interface_vcs_helper_v) \
		--git "$(GIT)" \
		--git-dir "$(dbus_api_git_dir)" \
		--git-work-tree "$(dbus_api_git_work_tree)" \
		--git-refs "$(dbus_api_git_refs)" \
		--git-remote "$(git_remote_origin)" \
		--no-push \
		install $(dbus_api_xml_files)
.PHONY: dbus-deviation-mk-install


# Helper for the pre-push git hook to export the configuration.
# Exports in bash syntax so this can be directly evaled.
dbus-deviation-mk-config:
	@echo "dbus_api_git_refs=\"$(dbus_api_git_refs)\""
	@echo "dbus_api_xml_files=\"$(dbus_api_xml_files)\""
.PHONY: dbus-deviation-mk-config
