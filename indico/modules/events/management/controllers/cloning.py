# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from collections import OrderedDict
from datetime import datetime

from dateutil import rrule
from flask import flash, jsonify, session, request
from pytz import utc
from werkzeug.exceptions import BadRequest

from indico.modules.events.cloning import EventCloner
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.management.forms import (CloneRepeatabilityForm,
                                                    CloneContentsForm, CloneCategorySelectForm, CloneRepeatOnceForm,
                                                    CloneRepeatIntervalForm, CloneRepeatPatternForm,
                                                    CLONE_REPEAT_CHOICES)
from indico.modules.events.operations import clone_event
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.util import jsonify_template, jsonify_data

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

    def _calc_stop_criteria(self, form):
        args = {}
        if form.stop_criterion.data == 'day':
            args['until'] = utc.localize(datetime.combine(form.until_dt.data, form.start_dt.data.time()))
        else:
            args['count'] = form.num_times.data
        return args

    def calculate(self, formdata):
        form = self.form_class(self.event, formdata=formdata)
        if form.validate():
            return self._calculate(form)
        else:
            raise ValueError([(unicode(getattr(form, k).label.text), v) for k, v in form.errors.viewitems()])


class PatternCloneCalculator(CloneCalculator):
    form_class = CloneRepeatPatternForm

    def _calculate(self, form):
        args = {'dtstart': form.start_dt.data}
        args.update(self._calc_stop_criteria(form))
        return list(rrule.rrule(rrule.MONTHLY, interval=form.num_months.data, byweekday=form.week_day.week_day_data,
                                bysetpos=form.week_day.day_number_data, **args))


class IntervalCloneCalculator(CloneCalculator):
    form_class = CloneRepeatIntervalForm

    def _calculate(self, form):
        args = {'dtstart': form.start_dt.data}
        args.update(self._calc_stop_criteria(form))
        freq, interval = relativedelta_to_rrule_interval(form.recurrence.data)
        return list(rrule.rrule(freq, interval=interval, **args))


class RHClonePreview(RHManageEventBase):
    ALLOW_LOCKED = True

    def _process(self):
        form = CloneRepeatabilityForm()
        clone_calculator = get_clone_calculator(form.repeatability.data, self.event_new)
        try:
            dates = clone_calculator.calculate(request.form)
            if len(dates) > 100:
                raise ValueError(_("You can clone maximum of 100 times at once"))
        except ValueError as e:
            return jsonify(error={'message': e.message})
        return jsonify_data(count=len(dates), dates=dates, flash=False)


class RHCloneEvent(RHManageEventBase):
    """Create copies of the event."""

    ALLOW_LOCKED = True

    def _form_for_step(self, step, set_defaults=True):
        if step == 1:
            return CloneRepeatabilityForm()
        elif step == 2:
            return CloneContentsForm(self.event_new, set_defaults=set_defaults)
        elif step == 3:
            default_category = (self.event_new.category if self.event_new.category.can_create_events(session.user)
                                else None)
            return CloneCategorySelectForm(self.event_new, category=default_category)
        elif step == 4:
            return REPEAT_FORM_MAP[request.form['repeatability']](self.event_new, set_defaults=set_defaults)
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
            form = REPEAT_FORM_MAP[request.form['repeatability']](self.event_new)

            if form.validate_on_submit():
                if form.repeatability.data == 'once':
                    dates = [form.start_dt.data]
                else:
                    clone_calculator = get_clone_calculator(form.repeatability.data, self.event_new)
                    dates = clone_calculator.calculate(request.form)
                clones = [clone_event(self.event_new, start_dt, set(form.selected_items.data), form.category.data)
                          for start_dt in dates]
                if len(clones) == 1:
                    flash(_('Welcome to your cloned event!'), 'success')
                    return jsonify_data(redirect=url_for('event_management.settings', clones[0]), flash=False)
                else:
                    flash(_('{} new events created.').format(len(dates)), 'success')
                    return jsonify_data(redirect=form.category.data.url, flash=False)
            else:
                # back to step 4, since there's been an error
                step = 4
        dependencies = {c.name: {'requires': list(c.requires_deep), 'required_by': list(c.required_by_deep)}
                        for c in EventCloner.get_cloners(self.event_new)}
        return jsonify_template('events/management/clone_event.html', event=self.event_new, step=step, form=form,
                                cloner_dependencies=dependencies, **tpl_args)
