# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.contributions.models.persons import (ContributionPersonLink, AuthorType,
                                                                SubContributionPersonLink)
from indico.modules.events.contributions.util import serialize_contribution_person_link
from indico.modules.users.models.users import UserTitle
from indico.util.i18n import _
from indico.web.forms.fields import EventPersonListField
from indico.web.forms.widgets import JinjaWidget


class ContributionPersonListField(EventPersonListField):
    """A field to configure a list of contribution persons"""

    widget = JinjaWidget('events/contributions/forms/contribution_person_widget.html')

    def __init__(self, *args, **kwargs):
        self.author_types = AuthorType.serialize()
        self.allow_authors = kwargs.pop('allow_authors', False)
        self.show_empty_coauthors = kwargs.pop('show_empty_coauthors', True)
        self.default_is_submitter = kwargs.pop('default_is_submitter', True)
        if self.allow_authors:
            self.default_author_type = kwargs.pop('default_author_type', AuthorType.primary)
            self.default_is_speaker = kwargs.pop('default_is_speaker', False)
        else:
            self.default_author_type = AuthorType.none
            self.default_is_speaker = True
        super(ContributionPersonListField, self).__init__(*args, **kwargs)

    def _convert_data(self, data):
        return {self._get_contribution_person(x): x.pop('isSubmitter', self.default_is_submitter) for x in data}

    @no_autoflush
    def _get_contribution_person(self, data):
        author_type = data.pop('authorType', self.default_author_type)
        is_speaker = data.pop('isSpeaker', self.default_is_speaker)
        person = self._get_event_person(data)
        title = next((x.value for x in UserTitle if data.get('title') == x.title), UserTitle.none)
        return ContributionPersonLink(person=person, first_name=data.get('firstName', ''), last_name=data['familyName'],
                                      title=title, affiliation=data.get('affiliation', ''),
                                      address=data.get('address', ''), phone=data.get('phone', ''),
                                      author_type=author_type, is_speaker=is_speaker)

    def _serialize_principal(self, principal):
        if not isinstance(principal, (ContributionPersonLink, SubContributionPersonLink)):
            return super(ContributionPersonListField, self)._serialize_principal(principal)
        else:
            return serialize_contribution_person_link(principal)

    def pre_validate(self, form):
        super(ContributionPersonListField, self).pre_validate(form)
        persons = set()
        for person_link in self.data:
            if person_link.person in persons:
                raise ValueError(_("Person with email '{}' is duplicated").format(person_link.person.email))
            if not self.allow_authors and person_link.author_type != AuthorType.none:
                raise ValueError(_("Author data received"))
            if person_link.author_type == AuthorType.none and not person_link.is_speaker:
                raise ValueError(_("{} has no role").format(person_link.full_name))
            persons.add(person_link.person)


class SubContributionPersonListField(ContributionPersonListField):
    """A field to configure a list of subcontribution persons"""

    def _get_contribution_person(self, data):
        return SubContributionPersonLink(person=self._get_event_person(data))
