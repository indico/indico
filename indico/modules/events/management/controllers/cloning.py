# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from collections import OrderedDict
from datetime import datetime, timedelta

from dateutil import rrule
from flask import flash, jsonify, request, session
from werkzeug.exceptions import BadRequest

from indico.modules.events.cloning import EventCloner
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.management.forms import (CLONE_REPEAT_CHOICES, CloneCategorySelectForm, CloneContentsForm,
                                                    CloneRepeatabilityForm, CloneRepeatIntervalForm,
                                                    CloneRepeatOnceForm, CloneRepeatPatternForm, ImportContentsForm,
                                                    ImportSourceEventForm)
from indico.modules.events.operations import clone_event, clone_into_event
from indico.modules.events.util import get_event_from_url
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.util import jsonify_data, jsonify_template


REPEAT_FORM_MAP = {
    'once': CloneRepeatOnceForm,
    'interval': CloneRepeatIntervalForm,
    'pattern': CloneRepeatPatternForm
}

RRULE_FREQ_MAP = OrderedDict([
    ('years', rrule.YEARLY),
    ('months', rrule.MONTHLY),
    ('weeks', rrule.WEEKLY),
    ('days', rrule.DAILY),
    ('hours', rrule.HOURLY),
    ('minutes', rrule.MINUTELY),
    ('seconds', rrule.SECONDLY)
])


def relativedelta_to_rrule_interval(rdelta):
    for unit, freq in RRULE_FREQ_MAP.viewitems():
        value = getattr(rdelta, unit)
        if value:
            return freq, value
    raise ValueError('Invalid relativedelta(...) object')


def get_clone_calculator(repeatability, event):
    if repeatability == 'interval':
        return IntervalCloneCalculator(event)
    elif repeatability == 'pattern':
        return PatternCloneCalculator(event)
    else:
        raise BadRequest


class CloneCalculator(object):
    def __init__(self, event):
        self.event = event

    def _naivify(self, dt):
        return dt.astimezone(self.event.tzinfo).replace(tzinfo=None)

    def _tzify(self, dates):
        return [self.event.tzinfo.localize(dt) for dt in dates]

    def _calc_stop_criteria(self, form):
        args = {}
        if form.stop_criterion.data == 'day':
            args['until'] = datetime.combine(form.until_dt.data, self._naivify(form.start_dt.data).time())
        else:
            args['count'] = form.num_times.data
        return args

    def calculate(self, formdata):
        """Calculate dates of cloned events.

        :return: a ``(dates, last_day_of_month)`` tuple
        """
        form = self.form_class(self.event, formdata=formdata)
        if form.validate():
            return self._calculate(form)
        else:
            raise ValueError([(unicode(getattr(form, k).label.text), v) for k, v in form.errors.viewitems()])


class PatternCloneCalculator(CloneCalculator):
    form_class = CloneRepeatPatternForm

    def _calculate(self, form):
        args = {'dtstart': self._naivify(form.start_dt.data)}
        args.update(self._calc_stop_criteria(form))
        dates = self._tzify(rrule.rrule(rrule.MONTHLY,
                                        interval=form.num_months.data,
                                        byweekday=form.week_day.week_day_data,
                                        bysetpos=form.week_day.day_number_data,
                                        **args))
        return dates, False


class IntervalCloneCalculator(CloneCalculator):
    form_class = CloneRepeatIntervalForm

    def _calculate(self, form):
        freq, interval = relativedelta_to_rrule_interval(form.recurrence.data)
        # check if last day of month
        dtstart = self._naivify(form.start_dt.data)
        next_day = dtstart + timedelta(days=1)
        if freq == rrule.MONTHLY and next_day.day == 1:
            kwargs = dict(self._calc_stop_criteria(form), dtstart=next_day)
            dates = rrule.rrule(freq, interval=interval, **kwargs)
            dates = self._tzify([date - timedelta(days=1) for date in dates])
            last_day_of_month = True
        else:
            kwargs = dict(self._calc_stop_criteria(form), dtstart=dtstart)
            dates = self._tzify(rrule.rrule(freq, interval=interval, **kwargs))
            last_day_of_month = False
        return dates, last_day_of_month


class RHClonePreview(RHManageEventBase):
    ALLOW_LOCKED = True

    def _process(self):
        form = CloneRepeatabilityForm()
        clone_calculator = get_clone_calculator(form.repeatability.data, self.event)
        try:
            dates, last_day_of_month = clone_calculator.calculate(request.form)
            if len(dates) > 100:
                raise ValueError(_("You can clone maximum of 100 times at once"))
        except ValueError as e:
            return jsonify(error={'message': e.message})
        return jsonify_data(count=len(dates), dates=dates, last_day_of_month=last_day_of_month, flash=False)


class RHCloneEvent(RHManageEventBase):
    """Create copies of the event."""

    ALLOW_LOCKED = True

    def _form_for_step(self, step, set_defaults=True):
        if step == 1:
            return CloneRepeatabilityForm()
        elif step == 2:
            return CloneContentsForm(self.event, set_defaults=set_defaults)
        elif step == 3:
            default_category = (self.event.category if self.event.category.can_create_events(session.user)
                                else None)
            return CloneCategorySelectForm(self.event, category=default_category)
        elif step == 4:
            return REPEAT_FORM_MAP[request.form['repeatability']](self.event, set_defaults=set_defaults)
        else:
            return None

    def _process(self):
        step = int(request.form.get('step', 1))
        tpl_args = {}
        form = self._form_for_step(step, set_defaults=True)
        prev_form = self._form_for_step(step - 1)

        if prev_form and not prev_form.validate():
            form = prev_form
            step = step - 1

        if step == 4:
            tpl_args.update({
                'step_title': dict(CLONE_REPEAT_CHOICES)[request.form['repeatability']],
            })
        elif step > 4:
            # last step - perform actual cloning
            form = REPEAT_FORM_MAP[request.form['repeatability']](self.event)

            if form.validate_on_submit():
                if form.repeatability.data == 'once':
                    # only one repetition
                    clone = clone_event(
                        self.event, None, form.start_dt.data, set(form.selected_items.data), form.category.data
                    )
                    flash(_('Welcome to your cloned event!'), 'success')
                    return jsonify_data(redirect=url_for('event_management.settings', clone), flash=False)
                else:
                    # recurring event
                    clone_calculator = get_clone_calculator(form.repeatability.data, self.event)
                    dates = clone_calculator.calculate(request.form)[0]
                    for n, start_dt in enumerate(dates, 1):
                        clone_event(self.event, n, start_dt, set(form.selected_items.data), form.category.data)
                    flash(_('{} new events created.').format(len(dates)), 'success')
                    return jsonify_data(redirect=form.category.data.url, flash=False)
            else:
                # back to step 4, since there's been an error
                step = 4
        dependencies = {c.name: {'requires': list(c.requires_deep), 'required_by': list(c.required_by_deep)}
                        for c in EventCloner.get_cloners(self.event)}
        return jsonify_template('events/management/clone_event.html', event=self.event, step=step, form=form,
                                cloner_dependencies=dependencies, **tpl_args)


def _get_import_source_from_url(target_event, url):
    event = get_event_from_url(url)
    if event == target_event:
        raise ValueError(_('Cannot import from the same event'))
    if event.type_ != target_event.type_:
        raise ValueError(_('Cannot import from a different type of event'))
    if not event.can_manage(session.user):
        raise ValueError(_('You do not have management rights to this event'))
    return event


class RHImportFromEvent(RHManageEventBase):
    """Import data from another event."""

    def _process_args(self):
        RHManageEventBase._process_args(self)
        url = request.form.get('source_event_url')
        self.source_event = _get_import_source_from_url(self.event, url) if url else None

    def _form_for_step(self, step, set_defaults=True):
        if step == 1:
            return ImportSourceEventForm()
        elif step == 2:
            return ImportContentsForm(self.source_event, self.event, set_defaults=set_defaults)
        else:
            return None

    def _process(self):
        step = int(request.form.get('step', 1))
        form = self._form_for_step(step, set_defaults=True)
        prev_form = self._form_for_step(step - 1)

        if prev_form and not prev_form.validate():
            form = prev_form
            step = step - 1

        elif step > 2:
            # last step - perform actual cloning
            form = ImportContentsForm(self.source_event, self.event)

            if form.validate_on_submit():
                updated_event = clone_into_event(self.source_event, self.event, set(form.selected_items.data))
                flash(_('Import successful!'), 'success')
                return jsonify_data(redirect=url_for('event_management.settings', updated_event), flash=False)
            else:
                # back to step 2, since there's been an error
                step = 2
        dependencies = {c.name: {'requires': list(c.requires_deep), 'required_by': list(c.required_by_deep)}
                        for c in EventCloner.get_cloners(self.event)}
        return jsonify_template('events/management/import_event.html', event=self.event, step=step, form=form,
                                cloner_dependencies=dependencies)


class RHImportEventDetails(RHManageEventBase):
    ALLOW_LOCKED = True

    def _process(self):
        from indico.modules.events.schemas import EventDetailsSchema
        schema = EventDetailsSchema()
        form = ImportSourceEventForm()
        try:
            event = _get_import_source_from_url(self.event, form.source_event_url.data)
        except ValueError as e:
            return jsonify(error={'message': e.message})
        return jsonify_data(event=schema.dump(event))
