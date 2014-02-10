# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.user import Avatar, Group
from MaKaC.conference import Category

from MaKaC.common.logger import Logger

class RecordingManagerMarcTagGenerator(object):

    @classmethod
    def generateAccessListXML(cls, out, obj):
        """Generate a comprehensive access list showing all users and e-groups who may access
        this object, taking into account the permissions and access lists of its owners.
        obj could be a Conference, Session, Contribution, or SubContribution object.
        This will become tag 506 after being XSL transformed."""

        allowed_users = obj.getRecursiveAllowedToAccessList()
        if allowed_users is not None and len(allowed_users) > 0:
            # Populate two lists holding email/group strings instead of Avatar/Group objects
            allowed_emails = []
            allowed_groups = []
            for user_obj in allowed_users:
                if isinstance(user_obj, Avatar):
                    allowed_emails.append(user_obj.getEmail())
                elif isinstance(user_obj, Group) and user_obj.groupType != "Default":
                    allowed_groups.append(user_obj.getId() + " [CERN]")
                else:
                    allowed_emails.append("UNKNOWN: %s" % user_obj.getId())

            # Create XML list of groups
            if len(allowed_groups) > 0:
                out.openTag("allowedAccessGroups")
                for group_id in allowed_groups:
                    out.writeTag("group", group_id)
                out.closeTag("allowedAccessGroups")

            # Create XML list of emails
            if len(allowed_users) > 0:
                out.openTag("allowedAccessEmails")
                for email_id in allowed_emails:
                    out.writeTag("email", email_id)
                out.closeTag("allowedAccessEmails")

    @classmethod
    def generateVideoXML(cls, out, recordingManagerTags):
        """Generate XML variables needed for video records."""

#        Logger.get('RecMan').info("in generateVideoXML(), contentType = %s" % recordingManagerTags["contentType"])
#        Logger.get('RecMan').info("in generateVideoXML(), contentType = %s" % recordingManagerTags["videoFormat"])

        # retrieve actual syntax to use from RecordingManager plug-in options.
        videoTagStandard      = CollaborationTools.getOptionValue("RecordingManager", "videoFormatStandard")
        videoTagWide          = CollaborationTools.getOptionValue("RecordingManager", "videoFormatWide")
        contentTypeWebLecture = CollaborationTools.getOptionValue("RecordingManager", "contentTypeWebLecture")

        # If it's plain video, specify whether standard or wide format
        if recordingManagerTags["contentType"] == 'plain_video':
            if recordingManagerTags["videoFormat"] == 'standard':
                out.writeTag("videoFormat", videoTagStandard)
            elif recordingManagerTags["videoFormat"] == 'wide':
                out.writeTag("videoFormat", videoTagWide)
        # if it's a web lecture, then specify that.
        elif recordingManagerTags["contentType"] == 'web_lecture':
            out.writeTag("videoFormat", contentTypeWebLecture)

    @classmethod
    def generateLanguagesXML(cls, out, recordingManagerTags):
        """Generate XML variables needed for language information."""

        if len(recordingManagerTags["languages"]) > 0:
            out.openTag("languages")
            for l in recordingManagerTags["languages"]:
#                Logger.get('RecMan').info("in generateLanguagesXML(), language = %s" % l)
                out.writeTag("code", l)
            out.closeTag("languages")

    @classmethod
    def generateCDSCategoryXML(cls, out, obj):
        """Determine if this record should belong to any particular CDS categories,
        based on the recursive list of owners and Recording Manager options.
        This will become MARC tag 980__a after XSL transformation."""

        # Each Indico category may be associated with up to 1 CDS categories,
        # but multiple Indico categories may be associated with the same CDS category.
        listCDSCategories = []

        # Get every successive owner of this object up to the root category.
        # If this object is more than 20 levels deep that would be CRAZY!
        crazyCounter = 0
        while obj is not None and crazyCounter < 20:
            #Logger.get('RecMan').debug("obj id: %s, title: \"%s\"" % (obj.getId(), obj.getTitle()))

            # getId() is not unique for all objects across the database. It is unique for all categories, though,
            # so as long as we are only dealing with categories it's ok.
            if CollaborationTools.getOptionValue("RecordingManager", "CDSCategoryAssignments").has_key(obj.getId()) \
                and CollaborationTools.getOptionValue("RecordingManager", "CDSCategoryAssignments")[obj.getId()] is not None \
                and isinstance(obj, Category):
                if CollaborationTools.getOptionValue("RecordingManager", "CDSCategoryAssignments")[obj.getId()] not in listCDSCategories:
                    listCDSCategories.append(CollaborationTools.getOptionValue("RecordingManager", "CDSCategoryAssignments")[obj.getId()])
                    #Logger.get('RecMan').debug("  This one matches! Appending \"%s\"" % CollaborationTools.getOptionValue("RecordingManager", "CDSCategoryAssignments")[obj.getId()])

            obj = obj.getOwner()
            crazyCounter += 1

        # Generate the base XML tags
        if len(listCDSCategories) > 0:
            out.openTag("CDSCategories")
            for category in listCDSCategories:
                out.writeTag("category", category)
            out.closeTag("CDSCategories")

    @classmethod
    def generateExperimentXML(cls, out, obj):
        """Determine if this record belongs to a particular experiment,
        based on the recursive list of owners and Recording Manager options.
        This will become tag 693__e after XSL transformation."""

        # Each Indico category may be associated with 1 experiment.
        experiment = None

        # Get every successive owner of this object up to the root category, stop if match is found.
        # If this object is more than 20 levels deep that would be CRAZY!
        crazyCounter = 0
        while obj is not None and crazyCounter < 20:
            #Logger.get('RecMan').debug("obj id: %s, title: \"%s\"" % (obj.getId(), obj.getTitle()))

            # getId() is not unique for all objects across the database. It is unique for all categories, though,
            # so as long as we are only dealing with categories it's ok.
            if CollaborationTools.getOptionValue("RecordingManager", "CDSExperimentAssignments").has_key(obj.getId()) \
                and CollaborationTools.getOptionValue("RecordingManager", "CDSExperimentAssignments")[obj.getId()] is not None \
                and isinstance(obj, Category):
                experiment = CollaborationTools.getOptionValue("RecordingManager", "CDSExperimentAssignments")[obj.getId()]
                #Logger.get('RecMan').debug("  This one matches! Experiment is \"%s\"" % experiment)
                break

            obj = obj.getOwner()
            crazyCounter += 1

        # Generate the base XML tags
        if experiment is not None:
            out.writeTag("CDSExperiment", experiment)
