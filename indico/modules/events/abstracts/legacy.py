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

from datetime import timedelta

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.abstracts.models.fields import AbstractFieldValue
from indico.modules.events.abstracts.models.judgments import Judgment
from indico.modules.events.abstracts.settings import abstracts_settings
from indico.modules.events.contributions import Contribution
from indico.modules.events.contributions.models.fields import ContributionField
from indico.modules.events.contributions.operations import create_contribution
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.contributions.models.persons import AuthorType, ContributionPersonLink
from indico.modules.users.models.users import User, UserTitle
from indico.util.caching import memoize_request
from indico.util.i18n import _
from indico.util.string import encode_utf8, to_unicode
from indico.util.text import wordsCounter

FIELD_TYPE_MAP = {
    'input': 'text',
    'textarea': 'text',
    'selection': 'single_choice'
}


@signals.event.contributions.contribution_deleted.connect
def _contribution_deleted(contrib, parent=None):
    from MaKaC.review import AbstractStatusAccepted, AbstractStatusSubmitted
    abstract = contrib.abstract
    if abstract:
        status = abstract.as_legacy.getCurrentStatus()
        if isinstance(status, AbstractStatusAccepted):
            if status.getTrack() is not None:
                abstract.as_legacy.addTrack(status.getTrack())
            abstract.as_legacy.setCurrentStatus(AbstractStatusSubmitted(abstract.as_legacy))
            abstract.contribution = None


def person_from_data(person_data, event):
    user = User.find_first(~User.is_deleted, User.all_emails.contains(person_data['email'].lower()))
    if user:
        return EventPerson.for_user(user, event)

    person = EventPerson.find_first(event_new=event, email=person_data['email'].lower())
    if not person:
        person = EventPerson(event_new=event, **person_data)
    return person


@no_autoflush
def contribution_from_abstract(abstract, sess):
    from MaKaC.review import AbstractStatusAccepted

    event = abstract.as_new.event_new
    duration = sess.default_contribution_duration if sess else timedelta(minutes=15)
    links = []

    for auth in abstract.getAuthorList():
        author_type = AuthorType.primary if abstract.isPrimaryAuthor(auth) else AuthorType.secondary
        person_data = {
            'title': UserTitle.from_legacy(to_unicode(auth.getTitle())),
            'email': to_unicode(auth.getEmail()),
            'address': to_unicode(auth.getAddress()),
            'affiliation': to_unicode(auth.getAffiliation()),
            'first_name': to_unicode(auth.getFirstName()),
            'last_name': to_unicode(auth.getSurName()),
            'phone': to_unicode(auth.getTelephone())
        }

        person = person_from_data(person_data, event)
        person_data.pop('email')
        links.append(ContributionPersonLink(author_type=author_type, person=person,
                                            is_speaker=abstract.isSpeaker(auth), **person_data))

    custom_fields_data = {'custom_{}'.format(field_val.contribution_field.id): field_val.data for
                          field_val in abstract.as_new.field_values}
    contrib = create_contribution(event, {'title': abstract.getTitle(), 'duration': duration,
                                          'person_link_data': {link: True for link in links}},
                                  custom_fields_data=custom_fields_data)
    contrib.abstract = abstract.as_new
    contrib.description = abstract.as_new.description

    # if this is an accepted abstract, set track and type if present
    status = abstract.getCurrentStatus()
    if isinstance(status, AbstractStatusAccepted):
        track = abstract.as_new.accepted_track
        contrib_type = abstract.as_new.accepted_type
        if track:
            contrib.track_id = int(track.getId())
        if contrib_type:
            contrib.type = contrib_type

    if sess:
        contrib.session = sess

    return contrib


class AbstractFieldWrapper(object):
    """Wraps an actual ``ContributionField`` in order to emulate the old ``AbstractField``s."""

    @classmethod
    def wrap(cls, field):
        if field.field_type == 'single_choice':
            return AbstractSelectionFieldWrapper(field)
        return AbstractTextFieldWrapper(field)

    def __init__(self, contrib_field):
        self.field = contrib_field

    def getType(self):
        field = self.field

        if field.field_type == 'text':
            return 'textarea' if field.field_data.get('multiline') else 'input'
        else:
            return 'selection'

    def isMandatory(self):
        return self.field.is_required

    def getId(self):
        return self.field.legacy_id or str(self.field.id)

    def getCaption(self):
        return self.field.title

    def isActive(self):
        return self.field.is_active

    def getValues(self):
        data = self.field.field_data
        data.update({
            'id': self.field.id,
            'caption': self.field.title.encode('utf-8'),
            'isMandatory': self.field.is_required
        })
        return data

    def check(self, content):
        if self.field.is_active and self.field.is_required and not content:
            return [_("The field '{}' is mandatory").format(self.field.title)]
        return []

    @property
    def _type(self):
        return self.getType()


class AbstractTextFieldWrapper(AbstractFieldWrapper):
    """Wraps legacy ``AbstractTextAreaField`` and ``AbstractInputField``."""

    @property
    def max_words(self):
        return self.field.field_data.get('max_words', 0)

    @property
    def max_length(self):
        return self.field.field_data.get('max_length', 0)

    def getLimitation(self):
        return 'chars' if self.max_words is None else 'words'

    def getMaxLength(self):
        max_length = self.max_words if self.max_length is None else self.max_length
        return max_length or 0

    def getValues(self):
        data = super(AbstractTextFieldWrapper, self).getValues()
        data.update({
            'maxLength': self.getMaxLength(),
            'limitation': self.getLimitation()
        })
        return data

    def check(self, content):
        errors = super(AbstractTextFieldWrapper, self).check(content)

        if self.max_words and wordsCounter(str(content)) > self.max_words:
            errors.append(_("The field '{}' cannot be more than {} words long").format(
                self.field.title, self.max_words))
        elif self.max_length and len(content) > self.max_length:
            errors.append(_("The field '{}' cannot be more than {} characters long").format(
                self.field.title, self.max_length))

        return errors


class AbstractDescriptionFieldProxy(object):
    """Simulates an ``AbstractTextField``"""

    def __init__(self, event):
        self.event = event

    @property
    def legacy_id(self):
        return 'content'

    @property
    def title(self):
        return _('Content')

    @property
    def is_active(self):
        return abstracts_settings.get(self.event, 'description_settings')['is_active']

    @property
    def field_type(self):
        return 'text'

    @property
    def field_data(self):
        settings = abstracts_settings.get(self.event, 'description_settings')
        return {
            'max_words': settings.get('max_words', 0),
            'max_length': settings.get('max_length', 0),
            'multiline': True
        }

    @property
    def is_required(self):
        return abstracts_settings.get(self.event, 'description_settings')['is_required']


class AbstractSelectionFieldWrapper(AbstractFieldWrapper):
    """Wraps legacy ``AbstractSelectionField``."""

    def getOption(self, option_id):
        return next((SelectedFieldOptionWrapper(option)
                     for option in self.field.field_data['options'] if option['id'] == option_id), None)

    def getOptions(self):
        return [SelectedFieldOptionWrapper(option) for option in self.field.field_data['options']]

    def getValues(self):
        data = super(AbstractSelectionFieldWrapper, self).getValues()
        data.update({
            'options': self.field.field_data['options']
        })
        return data

    def check(self, content):
        errors = super(AbstractSelectionFieldWrapper, self).check(content)

        if content:
            if not any(op for op in self.getOptions() if op.getId() == content):
                errors.append(_("The option with ID '{}' in the field {} doesn't exist").format(
                    content, self.field.title))

        return errors


class SelectedFieldOptionWrapper(object):
    """Wraps a selection field option."""

    def __init__(self, option):
        self.id = option['id']
        self.deleted = option['is_deleted']
        self.value = option['option']

    def __eq__(self, other):
        if isinstance(other, SelectedFieldOptionWrapper):
            return self.id == other.id
        return False

    def __hash__(self):
        return hash(self.id)

    def __unicode__(self):
        return self.value

    @encode_utf8
    def __str__(self):
        return unicode(self)

    def getValue(self):
        return self.value

    def getId(self):
        return self.id

    def isDeleted(self):
        return self.deleted


class AbstractFieldManagerAdapter(object):
    """
    Provides an interface that closely resembles the old AbstractFieldMgr.

    But actually returns stored ``ContributionField``s.
    """

    def __init__(self, event):
        self.event = event

    @property
    def description_field(self):
        return AbstractDescriptionFieldProxy(self.event)

    def _notifyModification(self):
        pass

    def hasField(self, field_id):
        if field_id == 'content':
            return True

        legacy = self.event.contribution_fields.filter_by(legacy_id=field_id)
        if legacy.count():
            return True
        else:
            return self.event.contribution_fields.filter_by(id=int(field_id)).count() > 0

    def getFieldById(self, field_id):
        if field_id == 'content':
            field = self.description_field
        else:
            field = self.event.contribution_fields.filter_by(legacy_id=field_id).first()
            if not field:
                field = self.event.contribution_fields.filter_by(id=int(field_id)).first()
        return AbstractFieldWrapper.wrap(field) if field else None

    def getFields(self):
        fields = [AbstractFieldWrapper.wrap(field) for field in self.event.contribution_fields]
        fields.append(AbstractFieldWrapper.wrap(AbstractDescriptionFieldProxy(self.event)))
        return fields

    def getActiveFields(self):
        fields = [AbstractFieldWrapper.wrap(field) for field in self.event.contribution_fields if field.is_active]
        fields.append(AbstractFieldWrapper.wrap(AbstractDescriptionFieldProxy(self.event)))
        return fields

    def hasActiveField(self, field_id):
        if field_id == 'content':
            return self.description_field.is_active
        return self.getFieldById(field_id).isActive() if self.getFieldById(field_id) else False

    def hasAnyActiveField(self):
        return (self.event.contribution_fields.filter(ContributionField.is_active).count() > 0 or
                self.description_field.is_active)

    def enableField(self, field_id):
        field = self.getFieldById(field_id)
        if field:
            field.is_active = True

    def disableField(self, field_id):
        field = self.getFieldById(field_id)
        if field:
            field.is_active = False


class AbstractDescriptionValue(object):
    """Simulates a ``ContributionFieldValue``."""

    def __init__(self, abstract):
        self.abstract = abstract

    @property
    def contribution_field(self):
        return AbstractDescriptionFieldProxy(self.abstract)

    @property
    def data(self):
        return self.abstract.description

    @data.setter
    def data(self, description):
        self.abstract.description = description


class AbstractLegacyMixin(object):
    """Implements legacy interface of ZODB ``Abstract`` object."""

    def _get_field_value(self, field_id):
        if field_id == 'content':
            return AbstractDescriptionValue(self.as_new)
        else:
            field = self.event.contribution_fields.filter_by(legacy_id=field_id).one()
            fval = AbstractFieldValue.find_first(contribution_field=field, abstract=self.as_new)
            if fval:
                return fval
            else:
                return AbstractFieldValue(contribution_field=field, abstract=self.as_new, data={})

    @property
    @memoize_request
    def event(self):
        return self._owner._owner.as_event

    @classmethod
    @memoize_request
    def all_for_event(cls, event):
        return {a.legacy_id: a for a in Abstract.find(event_new=event)}

    @property
    @memoize_request
    def as_new(self):
        return self.all_for_event(self.event)[int(self._id)]

    @no_autoflush
    def _add_judgment(self, legacy_judgment):
        judgment = Judgment(track_id=legacy_judgment._track.id, judge=legacy_judgment._responsible.user,
                            accepted_type=getattr(legacy_judgment, '_contribType', None))
        self.as_new.judgments.append(judgment)
        return judgment

    def _del_judgment(self, legacy_judgment):
        db.session.delete(legacy_judgment.as_new)
        db.session.flush()

    def getFields(self):
        data = {val.contribution_field.legacy_id: AbstractFieldContentWrapper(val)
                for val in self.as_new.field_values}
        data['content'] = self.as_new.description
        return data

    def getField(self, field_id):
        field_val = self._get_field_value(field_id)
        return AbstractFieldContentWrapper(field_val)

    def removeField(self, field_id):
        field_val = self._get_field_value(field_id)
        if field_val:
            self.as_new.field_values.remove(field_val)

    def setField(self, field_id, val):
        field_val = self._get_field_value(field_id)
        field_val.data = val

    def getContribType(self):
        return self.as_new.type


class AbstractFieldContentWrapper(object):
    """Emulates legacy ``AbstractFieldContent`` object."""

    def __init__(self, field_val):
        self.field_val = field_val

    @property
    def field(self):
        return self.field_val.contribution_field

    @property
    def value(self):
        return self.field_val.data

    def __eq__(self, other):
        if isinstance(other, AbstractFieldContentWrapper) and self.field.id == other.field.id:
            return self.field_val.data == other.data
        elif not isinstance(other, AbstractFieldContentWrapper):
            return self.field_val.data == other
        return False

    def __len__(self):
        return len(self.field_val.data)

    def __ne__(self, other):
        return not (self == other)

    @encode_utf8
    def __str__(self):
        if self.field.field_type == 'single_choice':
            return unicode(AbstractSelectionFieldWrapper(self.field).getOption(self.value))
        return unicode(self.value or '')


class AbstractManagerLegacyMixin(object):
    """Adds methods necessary to the creation of abstracts, from the legacy code."""

    def _new_abstract(self, legacy_abstract, abstract_data):
        Abstract(legacy_id=legacy_abstract.getId(), event_new=legacy_abstract.getConference().as_event)
        db.session.flush()

    def _remove_abstract(self, legacy_abstract):
        abstract = legacy_abstract.as_new
        # do not use relationshio or with_parent since the contribution
        # might have been soft-deleted and this does not show up in the
        # relationship anymore
        for contrib in Contribution.find(abstract=abstract):
            contrib.abstract = None

        for judgment in abstract.judgments:
            db.session.delete(judgment)
        db.session.delete(abstract)
        db.session.flush()


class AbstractStatusAcceptedLegacyMixin(object):
    def getType(self):
        return self._abstract.as_new.accepted_type

    def _setTrack(self, track):
        self._abstract.as_new.accepted_track_id = track.id

    def getTrack(self):
        return self._abstract.as_new.accepted_track


class AbstractJudgmentLegacyMixin(object):
    @property
    def as_new(self):
        return Judgment.find_one(
            track_id=self._track.id, judge=self._responsible.user, abstract_id=self._abstract.as_new.id)

    def getContribType(self):
        return self.as_new.accepted_type
