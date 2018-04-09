# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from indico.modules.events.abstracts.models.abstracts import AbstractState
from indico.util.i18n import _, orig_string
from indico.util.placeholders import Placeholder
from indico.web.flask.util import url_for


__all__ = ('EventTitlePlaceholder', 'EventURLPlaceholder', 'AbstractIDPlaceholder', 'AbstractTitlePlaceholder',
           'AbstractURLPlaceholder', 'AbstractTrackPlaceholder', 'AbstractSessionPlaceholder',
           'PrimaryAuthorsPlaceholder', 'CoAuthorsPlaceholder', 'SubmitterNamePlaceholder',
           'SubmitterFirstNamePlaceholder', 'SubmitterLastNamePlaceholder', 'SubmitterTitlePlaceholder',
           'TargetAbstractIDPlaceholder', 'TargetAbstractTitlePlaceholder', 'TargetSubmitterNamePlaceholder',
           'TargetSubmitterFirstNamePlaceholder', 'TargetSubmitterLastNamePlaceholder', 'JudgmentCommentPlaceholder',
           'ContributionTypePlaceholder', 'ContributionURLPlaceholder')


class EventTitlePlaceholder(Placeholder):
    name = 'event_title'
    description = _("The title of the event")

    @classmethod
    def render(cls, abstract):
        return abstract.event.title


class EventURLPlaceholder(Placeholder):
    name = 'event_url'
    description = _("The URL of the event")

    @classmethod
    def render(cls, abstract):
        return abstract.event.external_url


class AbstractIDPlaceholder(Placeholder):
    name = 'abstract_id'
    description = _("The ID of the abstract")

    @classmethod
    def render(cls, abstract):
        return unicode(abstract.friendly_id)


class AbstractTitlePlaceholder(Placeholder):
    name = 'abstract_title'
    description = _("The title of the abstract")

    @classmethod
    def render(cls, abstract):
        return abstract.title


class AbstractURLPlaceholder(Placeholder):
    advanced = True
    name = 'abstract_url'
    description = _("The direct URL of the abstract")

    @classmethod
    def render(cls, abstract):
        return url_for('abstracts.display_abstract', abstract, management=False, _external=True)


class AbstractTrackPlaceholder(Placeholder):
    name = 'abstract_track'
    description = _("The name of the destination track")

    @classmethod
    def render(cls, abstract):
        if abstract.state == AbstractState.accepted:
            return abstract.accepted_track.title if abstract.accepted_track else ''
        return ', '.join(t.title for t in abstract.submitted_for_tracks)


class AbstractSessionPlaceholder(Placeholder):
    name = 'abstract_session'
    description = _("The name of the destination session")

    @classmethod
    def render(cls, abstract):
        if abstract.contribution and abstract.contribution.session:
            return abstract.contribution.session.title
        return ''


class ContributionTypePlaceholder(Placeholder):
    name = 'contribution_type'
    description = _("The contribution type that is associated to the abstract")

    @classmethod
    def render(cls, abstract):
        if abstract.state == AbstractState.withdrawn:
            ctype = abstract.accepted_contrib_type or abstract.submitted_contrib_type
        elif abstract.state == AbstractState.accepted:
            ctype = abstract.accepted_contrib_type
        else:
            ctype = abstract.submitted_contrib_type
        return ctype.name if ctype else ''


class PrimaryAuthorsPlaceholder(Placeholder):
    name = 'primary_authors'
    description = _('The names of the primary authors (separated by commas)')

    @classmethod
    def render(cls, abstract):
        return ', '.join(author.full_name for author in abstract.primary_authors)


class CoAuthorsPlaceholder(Placeholder):
    name = 'co_authors'
    description = _('The names of the co-authors (separated by commas)')

    @classmethod
    def render(cls, abstract):
        return ', '.join(author.full_name for author in abstract.secondary_authors)


class SubmitterNamePlaceholder(Placeholder):
    name = 'submitter_name'
    description = _('The full name of the submitter, no title')

    @classmethod
    def render(cls, abstract):
        return abstract.submitter.full_name


class SubmitterFirstNamePlaceholder(Placeholder):
    advanced = True
    name = 'submitter_first_name'
    description = _('The first name of the submitter')

    @classmethod
    def render(cls, abstract):
        return abstract.submitter.first_name


class SubmitterLastNamePlaceholder(Placeholder):
    advanced = True
    name = 'submitter_last_name'
    description = _('The last name of the submitter')

    @classmethod
    def render(cls, abstract):
        return abstract.submitter.last_name


class SubmitterTitlePlaceholder(Placeholder):
    name = 'submitter_title'
    description = _('The title of the submitter (Dr, Prof., etc...)')

    @classmethod
    def render(cls, abstract):
        return orig_string(abstract.submitter.title)


class ContributionURLPlaceholder(Placeholder):
    advanced = True
    name = 'contribution_url'
    description = _('Contribution URL')

    @classmethod
    def render(cls, abstract):
        if abstract.contribution:
            return url_for('contributions.display_contribution', abstract.contribution, _external=True)
        return ''


class TargetAbstractIDPlaceholder(Placeholder):
    name = 'target_abstract_id'
    description = _("The ID of the target abstract (merge or duplicate)")

    @classmethod
    def render(cls, abstract):
        target = abstract.merged_into or abstract.duplicate_of
        return unicode(target.friendly_id) if target else ''


class TargetAbstractTitlePlaceholder(Placeholder):
    name = 'target_abstract_title'
    description = _("The title of the target abstract (merge or duplicate)")

    @classmethod
    def render(cls, abstract):
        target = abstract.merged_into or abstract.duplicate_of
        return target.title if target else ''


class TargetSubmitterNamePlaceholder(Placeholder):
    advanced = True
    name = 'target_submitter_name'
    description = _("The full name of the target abstract's submitter, no title (merge or duplicate)")

    @classmethod
    def render(cls, abstract):
        target = abstract.merged_into or abstract.duplicate_of
        return target.submitter.full_name if target else ''


class TargetSubmitterFirstNamePlaceholder(Placeholder):
    advanced = True
    name = 'target_submitter_first_name'
    description = _("The first name of the target abstract's submitter (merge or duplicate)")

    @classmethod
    def render(cls, abstract):
        target = abstract.merged_into or abstract.duplicate_of
        return target.submitter.first_name if target else ''


class TargetSubmitterLastNamePlaceholder(Placeholder):
    advanced = True
    name = 'target_submitter_last_name'
    description = _("The last name of the target abstract's submitter (merge or duplicate)")

    @classmethod
    def render(cls, abstract):
        target = abstract.merged_into or abstract.duplicate_of
        return target.submitter.last_name if target else ''


class JudgmentCommentPlaceholder(Placeholder):
    name = 'judgment_comment'
    description = _('Comments written by event organizer (upon final decision)')

    @classmethod
    def render(cls, abstract):
        return abstract.judgment_comment
