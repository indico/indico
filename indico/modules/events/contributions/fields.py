# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from wtforms import ValidationError

from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.contributions.models.persons import (AuthorType, ContributionPersonLink,
                                                                SubContributionPersonLink)
from indico.modules.events.fields import PersonLinkListFieldBase
from indico.util.i18n import _
from indico.web.forms.widgets import JinjaWidget


class ContributionPersonLinkListField(PersonLinkListFieldBase):
    """A field to configure a list of contribution persons."""

    person_link_cls = ContributionPersonLink
    linked_object_attr = 'contrib'
    widget = JinjaWidget('forms/person_link_widget.html', allow_empty_email=True)

    @property
    def roles(self):
        roles = [{'name': 'speaker', 'label': _('Speaker'), 'icon': 'microphone', 'default': self.default_is_speaker}]
        if self.allow_submitters:
            roles.append({'name': 'submitter', 'label': _('Submitter'), 'icon': 'paperclip',
                          'default': self.default_is_submitter})
        if self.allow_authors:
            roles += [
                {'name': 'primary', 'label': _('Author'), 'plural': _('Authors'), 'section': True,
                 'default': self.default_is_author},
                {'name': 'secondary', 'label': _('Co-author'), 'plural': _('Co-authors'), 'section': True},
            ]
        return roles

    def __init__(self, *args, **kwargs):
        self.allow_authors = kwargs.pop('allow_authors', kwargs['_form'].event.type == 'conference')
        self.allow_submitters = kwargs.pop('allow_submitters', True)
        self.default_is_author = kwargs.pop('default_is_author', False)
        self.default_is_speaker = kwargs.pop('default_is_speaker', True)
        self.default_is_submitter = kwargs.pop('default_is_submitter', True)
        self.empty_message = _('There are no authors')
        super().__init__(*args, **kwargs)

    def _convert_data(self, data):
        return {self._get_person_link(x): 'submitter' in x.get('roles', []) for x in data}

    @no_autoflush
    def _get_person_link(self, data):
        person_link = super()._get_person_link(data)
        roles = data.get('roles', [])
        person_link.is_speaker = 'speaker' in roles
        person_link.author_type = next((AuthorType.get(a) for a in roles if AuthorType.get(a)), AuthorType.none)
        return person_link

    def _serialize_person_link(self, principal):
        from indico.modules.events.persons.schemas import PersonLinkSchema
        data = PersonLinkSchema().dump(principal)
        data['roles'] = []
        if principal.is_speaker:
            data['roles'].append('speaker')
        is_submitter = (self.data[principal] if self.get_form().is_submitted()
                        else principal.contribution and principal.is_submitter)
        data['roles'].append(principal.author_type.name)
        if is_submitter:
            data['roles'].append('submitter')
        return data

    def pre_validate(self, form):
        super().pre_validate(form)
        for person_link in self.data:
            if not self.allow_authors and person_link.author_type != AuthorType.none:
                if not self.object_data or person_link not in self.object_data:
                    person_link.author_type = AuthorType.none
            if person_link.author_type == AuthorType.none and not person_link.is_speaker:
                raise ValidationError(_('{} has no role').format(person_link.full_name))


class SubContributionPersonLinkListField(ContributionPersonLinkListField):
    """A field to configure a list of subcontribution persons."""

    person_link_cls = SubContributionPersonLink
    linked_object_attr = 'subcontrib'
    widget = JinjaWidget('forms/person_link_widget.html', allow_empty_email=True)

    def _serialize_person_link(self, principal):
        from indico.modules.events.persons.schemas import PersonLinkSchema
        data = PersonLinkSchema().dump(principal)
        data['roles'] = []
        if principal.is_speaker:
            data['roles'].append('speaker')
        return data
