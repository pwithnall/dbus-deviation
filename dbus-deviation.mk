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

# This Makefile can be included in the top-level Makefile.am in a project to
# provide rules for checking the API compatibility of D-Bus interface between
# different tagged releases of a project.
#
# To add it to your project, copy this file into your project, add it to git,
# and add the following lines to your top-level Makefile.am:
#
#    dbus_api_xml_files = list of D-Bus interface XML files
#    -include $(top_srcdir)/dbus-deviation.mk
#
# Further configuration options are documented below.
#
# Then, run the following command to initialise the database of past versions
# of the XML files:
#
#    make dbus-deviation-mk-install
#
# It is safe to run this command multiple times, though there is no need to.
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

# Mandatory configuration.
dbus_api_xml_files ?=

# Optional configuration.
git_remote_origin ?= origin
dbus_api_diff_warnings ?= info,forwards-compatibility,backwards-compatibility
dbus_api_git_refs ?= notes/dbus/api
dbus_api_git_work_tree ?= $(top_srcdir)
dbus_api_git_dir ?= $(dbus_api_git_work_tree)/.git
GIT = git

# Silent rules for dbus-interface-vcs-helper
helper_v = $(helper_v_@AM_V@)
helper_v_ = $(helper_v_@AM_DEFAULT_V@)
helper_v_0 = --silent
helper_v_1 =

V_api = $(v_api_@AM_V@)
v_api_ = $(v_api_@AM_DEFAULT_V@)
v_api_0 = @echo "  API     " $@;
v_api_1 =


# For each XML file in $(dbus_api_xml_files), add it to the API signature
# database for the most recent git tag.
dist-dbus-api-compatibility:
	$(V_api)dbus-interface-vcs-helper $(helper_v) \
		--git "$(GIT)" \
		--git-dir "$(dbus_api_git_dir)" \
		--git-work-tree "$(dbus_api_git_work_tree)" \
		--git-refs "$(dbus_api_git_refs)" \
		--git-remote "$(git_remote_origin)" \
		dist $(dbus_api_xml_files)
dist-hook: dist-dbus-api-compatibility
.PHONY: dist-dbus-api-compatibility


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
check-dbus-api-compatibility:
	$(V_api)dbus-interface-vcs-helper $(helper_v) \
		--git "$(GIT)" \
		--git-dir "$(dbus_api_git_dir)" \
		--git-work-tree "$(dbus_api_git_work_tree)" \
		--git-refs "$(dbus_api_git_refs)" \
		--git-remote "$(git_remote_origin)" \
		check \
		--diff-warnings "$(dbus_api_diff_warnings)" \
		"$(OLD_REF)" "$(NEW_REF)"
check-local: check-dbus-api-compatibility
.PHONY: check-dbus-api-compatibility


# Installation rule to set up an API signature database for each existing tag.
# It is safe to run this multiple times.
dbus-deviation-mk-install:
	$(V_api)dbus-interface-vcs-helper $(helper_v) \
		--git "$(GIT)" \
		--git-dir "$(dbus_api_git_dir)" \
		--git-work-tree "$(dbus_api_git_work_tree)" \
		--git-refs "$(dbus_api_git_refs)" \
		--git-remote "$(git_remote_origin)" \
		install $(dbus_api_xml_files)
.PHONY: dbus-deviation-mk-install
