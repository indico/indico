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

import itertools
from collections import OrderedDict

from indico.modules.events.abstracts.models.abstracts import AbstractState
from indico.util.i18n import _
from indico.util.rules import Condition, check_rule, get_missing_conditions


class EmailNotificationCondition(Condition):
    #: Override if you want to customize the text
    #: that shouls up for "Any"
    any_caption = _("any")
    #: same for text that shows up for "none"
    none_caption = _("none")
    #: Text that will show inline in rule descriptions
    label_text = None

    @classmethod
    def get_available_values(cls, event=None, **kwargs):
        choices = cls._iter_available_values(event=event, **kwargs)
        if not cls.required:
            return OrderedDict(itertools.chain([('*', cls.any_caption), ('', cls.none_caption)], choices))
        else:
            return OrderedDict(choices)

    @classmethod
    def _iter_available_values(cls, event, **kwargs):
        raise NotImplemented


class TrackCondition(EmailNotificationCondition):
    """A condition that matches a particular track."""

    name = 'track'
    description = _("Destination Track")
    any_caption = _("any track")
    none_caption = _("no track")
    label_text = _("in")

    @classmethod
    def _iter_available_values(cls, event, **kwargs):
        return ((t.id, t.title) for t in event.tracks)

    @classmethod
    def check(cls, values, abstract, **kwargs):
        if abstract.state == AbstractState.accepted:
            return abstract.accepted_track_id in values
        else:
            return bool(set(values) & {track.id for track in abstract.submitted_for_tracks})


class StateCondition(EmailNotificationCondition):
    """A condition that matches a particular abstract final state."""

    name = 'state'
    description = _("Final State")
    required = True

    compatible_with = {
        AbstractState.submitted.value: (),
        AbstractState.rejected.value: (),
        AbstractState.accepted.value: ('contribution_type', 'track'),
        AbstractState.merged.value: ('contribution_type', 'track'),
        AbstractState.duplicate.value: ('contribution_type', 'track'),
        AbstractState.withdrawn.value: ()
    }

    @classmethod
    def _iter_available_values(cls, **kwargs):
        return ((s.value, s.title) for s in AbstractState)

    @classmethod
    def check(cls, values, abstract, **kwargs):
        return abstract.state in values


class ContributionTypeCondition(EmailNotificationCondition):
    """"A condition that matches a particular contribution type."""

    name = 'contribution_type'
    description = _("Contribution Type")
    any_caption = _("any type")
    none_caption = _("no type")
    label_text = _("as")

    @classmethod
    def _iter_available_values(cls, event, **kwargs):
        return ((ct.id, ct.name) for ct in event.contribution_types)

    @classmethod
    def check(cls, values, abstract, **kwargs):
        if abstract.state == AbstractState.accepted:
            return abstract.accepted_contrib_type_id in values
        else:
            return abstract.submitted_contrib_type_id in values


def send_abstract_notifications(abstract):
    """Send abstract notification e-mails.

    :param abstract: the abstract that is going to be checked
                     against the event's notification rules
    """
    for tpl in abstract.event_new.abstract_email_templates:
        for rule in tpl.rules:
            if check_rule('abstract-notification-email', rule, abstract=abstract):
                pass
                # TODO: Actually send an e-mail in case there's a match
