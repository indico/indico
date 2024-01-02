# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.management.settings import program_codes_settings
from indico.util.date_time import format_datetime
from indico.util.i18n import _
from indico.util.placeholders import ParametrizedPlaceholder, Placeholder, get_empty_placeholders, replace_placeholders


def generate_program_codes(event, object_type, objects):
    if object_type == 'contributions':
        kwarg = 'contribution'
        context = 'program-codes-contribution'
        template_setting = 'contribution_template'
    elif object_type == 'subcontributions':
        kwarg = 'subcontribution'
        context = 'program-codes-subcontribution'
        template_setting = 'subcontribution_template'
    elif object_type == 'sessions':
        kwarg = 'session'
        context = 'program-codes-session'
        template_setting = 'session_template'
    elif object_type == 'session-blocks':
        kwarg = 'session_block'
        context = 'program-codes-session-block'
        template_setting = 'session_block_template'
    else:
        raise ValueError(f'Invalid object type: {object_type}')

    template = program_codes_settings.get(event, template_setting)
    return {
        obj: (replace_placeholders(context, template, escape_html=False, **{kwarg: obj}),
              get_empty_placeholders(context, template, **{kwarg: obj}))
        for obj in objects
    }


def _make_date_placeholder(class_name, name, render_kwarg, date_format, description, transform=None):
    dct = {'name': name, 'description': description, 'render_kwarg': render_kwarg, 'date_format': date_format,
           'transform': staticmethod(transform) if transform else None}
    return type(class_name, (DatePlaceholder,), dct)


class ContributionIDPlaceholder(ParametrizedPlaceholder):
    name = 'id'
    description = _('The ID of the contribution (optionally padded with zeros, e.g. {id:2} for "01" or {id} for "1")')
    param_friendly_name = 'length'
    param_required = False

    @classmethod
    def render(cls, param, contribution):
        if param is None:
            return str(contribution.friendly_id)
        try:
            padding = max(1, min(int(param), 10))
        except ValueError:
            return str(contribution.friendly_id)
        else:
            return str(contribution.friendly_id).zfill(padding)


class ContributionSessionCodePlaceholder(Placeholder):
    name = 'session_code'
    description = _("The program code of the contribution's session")

    @classmethod
    def render(cls, contribution):
        return contribution.session.code if contribution.session else ''


class ContributionSessionBlockCodePlaceholder(Placeholder):
    name = 'session_block_code'
    description = _("The program code of the contribution's session block")

    @classmethod
    def render(cls, contribution):
        return contribution.session_block.code if contribution.session_block else ''


class ContributionTrackCodePlaceholder(Placeholder):
    name = 'track_code'
    description = _("The program code of the contribution's track")

    @classmethod
    def render(cls, contribution):
        return contribution.track.code if contribution.track else ''


class DatePlaceholder(Placeholder):
    date_format = None

    @classmethod
    def render(cls, **kwargs):
        arg = kwargs.pop(cls.render_kwarg)
        if kwargs:
            raise TypeError(f'render() got unexpected kwargs: {kwargs}')
        if not arg.start_dt:
            return ''
        formatted = format_datetime(arg.start_dt, cls.date_format, locale='en_GB', timezone=arg.event.tzinfo)
        return cls.transform(formatted) if cls.transform else formatted


ContributionYearPlaceholder = _make_date_placeholder(
    'ContributionYearPlaceholder', 'year', 'contribution', 'yyyy',
    _('The year of the contribution')
)
ContributionMonthPlaceholder = _make_date_placeholder(
    'ContributionMonthPlaceholder', 'month', 'contribution', 'MM',
    _('The month of the contribution')
)
ContributionDayPlaceholder = _make_date_placeholder(
    'ContributionDayPlaceholder', 'day', 'contribution', 'dd',
    _('The day of the contribution')
)
ContributionWeekday2Placeholder = _make_date_placeholder(
    'ContributionWeekday2Placeholder', 'weekday2', 'contribution', 'EEEE',
    _('The weekday of the contribution (e.g. "TU")'),
    lambda x: x[:2].upper()
)
ContributionWeekday3Placeholder = _make_date_placeholder(
    'ContributionWeekday3Placeholder', 'weekday3', 'contribution', 'EEEE',
    _('The weekday of the contribution (e.g. "TUE")'),
    lambda x: x[:3].upper()
)


class SubContributionIDPlaceholder(Placeholder):
    name = 'id'
    description = _('The ID of the subcontribution')

    @classmethod
    def render(cls, subcontribution):
        return str(subcontribution.friendly_id)


class SubContributionContributionCodePlaceholder(Placeholder):
    name = 'contribution_code'
    description = _("The program code of the subcontribution's contribution")

    @classmethod
    def render(cls, subcontribution):
        return subcontribution.contribution.code


class SessionIDPlaceholder(Placeholder):
    name = 'id'
    description = _('The ID of the session')

    @classmethod
    def render(cls, session):
        return str(session.friendly_id)


class SessionSessionTypeCodePlaceholder(Placeholder):
    name = 'session_type_code'
    description = _("The program code of the session's session type")

    @classmethod
    def render(cls, session):
        return session.type.code if session.type else ''


class SessionBlockSessionCodePlaceholder(Placeholder):
    name = 'session_code'
    description = _("The program code of the session block's session")

    @classmethod
    def render(cls, session_block):
        return session_block.session.code


SessionBlockYearPlaceholder = _make_date_placeholder(
    'SessionBlockYearPlaceholder', 'year', 'session_block', 'yyyy',
    _('The year of the session block')
)
SessionBlockMonthPlaceholder = _make_date_placeholder(
    'SessionBlockMonthPlaceholder', 'month', 'session_block', 'MM',
    _('The month of the session block')
)
SessionBlockDayPlaceholder = _make_date_placeholder(
    'SessionBlockDayPlaceholder', 'day', 'session_block', 'dd',
    _('The day of the session block')
)
SessionBlockWeekday2Placeholder = _make_date_placeholder(
    'SessionBlockWeekday2Placeholder', 'weekday2', 'session_block', 'EEEE',
    _('The weekday of the session block (e.g. "TU")'),
    lambda x: x[:2].upper()
)
SessionBlockWeekday3Placeholder = _make_date_placeholder(
    'SessionBlockWeekday3Placeholder', 'weekday3', 'session_block', 'EEEE',
    _('The weekday of the session block (e.g. "TUE")'),
    lambda x: x[:3].upper()
)
