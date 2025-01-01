// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {Form, Input, Radio, Select} from 'semantic-ui-react';

import {WeekdayRecurrencePicker} from 'indico/modules/rb/components/WeekdayRecurrencePicker';
import {PluralTranslate, Translate} from 'indico/react/i18n';

import {FilterFormComponent} from '../../../common/filters';

import './RecurrenceForm.module.scss';

export default class RecurrenceForm extends FilterFormComponent {
  static propTypes = {
    type: PropTypes.string,
    interval: PropTypes.string,
    number: PropTypes.number,
    weekdays: PropTypes.arrayOf(PropTypes.string),
    ...FilterFormComponent.propTypes,
  };

  static defaultProps = {
    type: null,
    interval: null,
    number: null,
    weekdays: [],
  };

  componentDidUpdate() {
    this.preselectWeekdayToday();
  }

  constructor(props) {
    super(props);
    this.onTypeChange = e => {
      this.stateChanger('type')(e.target.value);
    };
    this.onTypeChange = this.stateChanger('type');
    this.onNumberChange = this.stateChanger('number', num => Math.abs(parseInt(num, 10)));
    this.onIntervalChange = this.stateChanger('interval');
    this.onWeekdaysChange = this.stateChanger('weekdays');
  }

  stateChanger(param, sanitizer = v => v) {
    const {setParentField} = this.props;
    return (_, {value}) => {
      value = sanitizer(value);
      // update both internal state (for rendering purposes and that of the parent)
      setParentField(param, value);
      this.setState({
        [param]: value,
      });
    };
  }

  preselectWeekdayToday() {
    const {weekdays, type, interval} = this.state;
    const today = moment()
      .locale('en')
      .format('ddd')
      .toLocaleLowerCase();

    if (interval !== 'week') {
      // If the interval is not 'week', clear weekdays
      if (weekdays.length > 0) {
        this.props.setParentField('weekdays', []);
      }
    } else if (weekdays.length === 0 && type === 'every') {
      // Preselect today if no weekday is selected
      this.setState({
        weekdays: [today],
      });
      this.props.setParentField('weekdays', [today]);
    } else if (weekdays.length > 0 && type !== 'every') {
      // Clear weekdays if type is not every
      this.props.setParentField('weekdays', []);
    }
  }

  render() {
    const {type, interval, number, weekdays} = this.state;
    const intervalOptions = [
      {
        value: 'week',
        text: PluralTranslate.string('Week', 'Weeks', number),
      },
      {
        value: 'month',
        text: PluralTranslate.string('Month', 'Months', number),
      },
    ];

    return (
      <Form>
        <Form.Field>
          <Radio
            value="single"
            name="type"
            checked={type === 'single'}
            label={Translate.string('Single booking')}
            onChange={this.onTypeChange}
          />
        </Form.Field>
        <Form.Field style={{marginBottom: '0.5em'}}>
          <Radio
            value="daily"
            name="type"
            checked={type === 'daily'}
            label={Translate.string('Daily')}
            onChange={this.onTypeChange}
          />
        </Form.Field>
        <Form.Group inline styleName="recurrence-every" style={{marginBottom: '1em'}}>
          <Form.Field>
            <Radio
              value="every"
              name="type"
              checked={type === 'every'}
              label={Translate.string('Every', 'Repetition')}
              onChange={this.onTypeChange}
            />
          </Form.Field>
          <Form.Field>
            <Input
              value={number}
              type="number"
              min="1"
              max="99"
              step="1"
              disabled={type !== 'every'}
              onChange={this.onNumberChange}
            />
          </Form.Field>
          <Form.Field style={{paddingRight: 0}}>
            <Select
              value={interval}
              disabled={type !== 'every'}
              onChange={this.onIntervalChange}
              options={intervalOptions}
            />
          </Form.Field>
        </Form.Group>
        {type === 'every' && interval === 'week' && (
          <Form.Field styleName="weekday-recurrence-section" inline>
            <label>
              <Translate>Recurring every</Translate>
            </label>
            <WeekdayRecurrencePicker
              onChange={value => this.onWeekdaysChange(null, {value})}
              value={weekdays}
              disabled={type !== 'every'}
              requireOneSelected
            />
          </Form.Field>
        )}
      </Form>
    );
  }
}
