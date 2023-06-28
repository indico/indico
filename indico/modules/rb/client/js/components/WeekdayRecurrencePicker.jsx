// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React from 'react';
import {Button, Icon, Message} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

function validate({selectedDays}) {
  const errors = {};
  if (Object.keys(selectedDays).length === 0) {
    errors.weekdays = Translate.string('You must select at least one weekday');
  }
  return errors;
}

class WeekdayRecurrencePicker extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      selectedDays: {},
      errors: {},
      messageState: {
        visible: true,
      },
    };
    this.delayTimeout = null;
  }

  componentDidMount() {
    this.preselectFirstWeekday();
  }

  componentWillUmount() {
    if (this.delayTimeout) {
      clearTimeout(this.delayTimeout);
    }
  }

  preselectFirstWeekday = () => {
    const firstWeekday = moment()
      .weekday(0)
      .locale('en')
      .format('ddd')
      .toLowerCase();

    this.setState(prevState => ({
      selectedDays: {
        ...prevState.selectedDays,
        [firstWeekday]: true,
      },
    }));
  };

  handleDayClick = day => {
    this.setState(
      prevState => {
        const selectedDays = {...prevState.selectedDays};
        if (selectedDays[day]) {
          delete selectedDays[day];
        } else {
          selectedDays[day] = true;
        }
        return {selectedDays};
      },
      () => {
        clearTimeout(this.delayTimeout);
        this.validateSelectedDays();
      }
    );
  };

  validateSelectedDays = () => {
    const {selectedDays, messageState} = this.state;
    const errors = validate({selectedDays});
    this.setState({errors});

    if (Object.keys(selectedDays).length === 0) {
      clearTimeout(this.delayTimeout);
      this.delayTimeout = setTimeout(() => {
        this.preselectFirstWeekday();
      }, 250);
    } else {
      clearTimeout(this.delayTimeout);
      this.setState({errors: {}});
      messageState.visible = true;
    }
  };

  handleMessageDismiss = () => {
    const {messageState} = this.state;
    messageState.visible = false;
    clearTimeout(this.delayTimeout);
    this.setState({errors: {}});
  };

  render() {
    const WEEKDAYS = moment.weekdays(true).map(weekday => {
      return {
        value: moment()
          .day(weekday)
          .locale('en')
          .format('ddd')
          .toLowerCase(),
        text: moment()
          .isoWeekday(weekday)
          .format('ddd'),
      };
    });

    const {selectedDays, errors, messageState} = this.state;

    return (
      <div>
        <Button.Group>
          {WEEKDAYS.map(weekday => (
            <Button
              key={weekday.value}
              value={weekday.value}
              compact
              className={selectedDays[weekday.value] ? 'primary' : ''}
              onClick={() => this.handleDayClick(weekday.value)}
            >
              {weekday.text}
            </Button>
          ))}
        </Button.Group>
        {errors.weekdays && messageState.visible && (
          <Message color="yellow" onDismiss={this.handleMessageDismiss}>
            <Icon name="warning circle" />
            {errors.weekdays}
          </Message>
        )}
      </div>
    );
  }
}

export default WeekdayRecurrencePicker;
