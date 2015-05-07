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
#    dbus_api_git_refs=notes/dbus/introspection  # matches the Makefile config
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
#    dbus_api_git_refs (default: notes/dbus/introspection):
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
dbus_api_git_refs ?= notes/dbus/introspection
GIT = git

# Needed for the process substitution in check-dbus-api-compatibility.
SHELL=/bin/bash


# For each XML file in $(dbus_api_xml_files), add it to the API signature
# database for the most recent git tag.
dist-dbus-api-compatibility:
	$(AM_V_at)latest_tag="$$($(GIT) describe --tags `$(GIT) rev-list --tags --max-count=1`)"; \
	for introspection_xml_file in $(dbus_api_xml_files); do \
		notes=$$($(GIT) rev-parse --verify --quiet "$$latest_tag^{tag}":"$$introspection_xml_file"); \
		introspection_xml_basename=$$(basename "$$introspection_xml_file"); \
		$(GIT) notes --ref "refs/$(dbus_api_git_refs)/$$introspection_xml_basename" add -C "$$notes" "$$latest_tag"; \
	done
	$(AM_V_at)$(GIT) push "$(git_remote_origin)" refs/$(dbus_api_git_refs)/*

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
	$(AM_V_at)if [ "$(OLD_REF)" != "" ] && ! $(GIT) rev-parse --verify "$(OLD_REF)" &> /dev/null; then \
		echo "error: Invalid OLD_REF." >&2; \
		exit 1; \
	fi
	$(AM_V_at)if [ "$(NEW_REF)" != "" ] && ! $(GIT) rev-parse --verify "$(NEW_REF)" &> /dev/null; then \
		echo "error: Invalid NEW_REF." >&2; \
		exit 1; \
	fi
	$(AM_V_at)$(GIT) fetch "$(git_remote_origin)" refs/$(dbus_api_git_refs)/*:refs/$(dbus_api_git_refs)/*
	$(AM_V_at)old_ref="$(OLD_REF)"; \
	new_ref="$(NEW_REF)"; \
	\
	if [ "$$old_ref" = "" ]; then \
		old_ref="$$($(GIT) describe --tags `$(GIT) rev-list --tags --max-count=1`)"; \
	fi; \
	\
	$(GIT) for-each-ref --shell --format="note_ref=%(refname)" refs/$(dbus_api_git_refs) | \
		while read entry; do \
			eval "$$entry"; \
			introspection_xml_file_basename="$$(basename "$$note_ref")"; \
			if $(AM_V_P); then \
				echo "Comparing $$introspection_xml_file_basename"; \
			else \
				echo " DIFF      $$introspection_xml_file_basename"; \
			fi; \
			\
			if [ "$$new_ref" = "" ]; then \
				# Debug output. Can't get `set -v` to do this usefully. \
				if $(AM_V_P); then \
					echo -e "dbus-interface-diff --warnings \"$(dbus_api_diff_warnings)\" \\\\\n\t<($(GIT) notes --ref \"$$note_ref\" show \"$$old_ref\" || echo \"\") \\\\\n\t\`$(GIT) ls-files \"*/$$introspection_xml_file_basename\"\`"; \
				fi; \
				\
				dbus-interface-diff --warnings "$(dbus_api_diff_warnings)" \
					<($(GIT) notes --ref "$$note_ref" show "$$old_ref" 2> /dev/null || echo "") \
					`$(GIT) ls-files "*/$$introspection_xml_file_basename"`; \
			else \
				# Debug output. \
				if $(AM_V_P); then \
					echo -e "dbus-interface-diff --warnings \"$(dbus_api_diff_warnings)\" \\\\\n\t<($(GIT) notes --ref \"$$note_ref\" show \"$$old_ref\" || echo \"\") \\\\\n\t<($(GIT) notes --ref \"$$note_ref\" show \"$$new_ref\" || echo \"\")"; \
				fi; \
				\
				dbus-interface-diff --warnings "$(dbus_api_diff_warnings)" \
					<($(GIT) notes --ref "$$note_ref" show "$$old_ref" 2> /dev/null || echo "") \
					<($(GIT) notes --ref "$$note_ref" show "$$new_ref" 2> /dev/null || echo ""); \
			fi \
		done

check-local: check-dbus-api-compatibility
.PHONY: check-dbus-api-compatibility


# Installation rule to set up an API signature database for each existing tag.
# It is safe to run this multiple times.
dbus-deviation-mk-install:
	$(AM_V_at)$(GIT) tag | \
		while read tag; do \
			outputted=0; \
			for introspection_xml_file in $(dbus_api_xml_files); do \
				notes=$$($(GIT) rev-parse --verify --quiet "$$tag^{tag}":"$$introspection_xml_file"); \
				if [ "$$notes" != "" ]; then \
					introspection_xml_basename=$$(basename "$$introspection_xml_file"); \
					if $(GIT) notes --ref "refs/$(dbus_api_git_refs)/$$introspection_xml_basename" add -C "$$notes" "$$tag" 2> /dev/null; then \
						echo "$$tag: Added note $$notes for XML file $$introspection_xml_basename"; \
						outputted=1; \
					fi \
				fi \
			done; \
			\
			if [ $$outputted == 0 ]; then \
				echo "$$tag: Nothing to do"; \
			fi \
		done
	$(AM_V_at)$(GIT) push "$(git_remote_origin)" refs/$(dbus_api_git_refs)/*

.PHONY: dbus-deviation-mk-install
