// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import TimePicker from 'rc-time-picker';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Accordion, Form, Icon} from 'semantic-ui-react';

import {FinalCheckbox, FinalField, FinalSubmitButton} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {entrySchema, handleUnimplemented} from '../util';

function TimePickerField({value, onChange, uses24HourFormat}) {
  return (
    <Form.Field>
      <TimePicker
        showSecond={false}
        value={moment(value)}
        focusOnOpen
        format={uses24HourFormat ? 'H:mm' : 'h:mm a'}
        onChange={onChange}
        use12Hours={!uses24HourFormat}
        allowEmpty={false}
        getPopupContainer={node => node}
      />
    </Form.Field>
  );
}

TimePickerField.propTypes = {
  value: PropTypes.instanceOf(Date).isRequired,
  onChange: PropTypes.func.isRequired,
  uses24HourFormat: PropTypes.bool.isRequired,
};

function TimeEditForm({entry, uses24HourFormat}) {
  const {start, end} = entry;
  // TODO implement
  const onSubmit = handleUnimplemented;
  return (
    <FinalForm
      onSubmit={onSubmit}
      initialValues={{
        start,
        duration: new Date(0, 0, 0, 0, moment(end).diff(start, 'minutes')),
        shift: false,
      }}
      initialValuesEqual={_.isEqual}
    >
      {({handleSubmit}) => (
        <Form id="time-edit-form" onSubmit={handleSubmit}>
          <Form.Group>
            <FinalField
              name="start"
              label={Translate.string('Start time')}
              component={TimePickerField}
              uses24HourFormat={uses24HourFormat}
            />
            <FinalField
              name="duration"
              label={Translate.string('Duration')}
              component={TimePickerField}
              uses24HourFormat={uses24HourFormat}
            />
          </Form.Group>
          <FinalCheckbox
            name="shift"
            label={Translate.string('Shift')}
            description={Translate.string('Shift all entries after this one up or down')}
          />
          <FinalSubmitButton form="time-edit-form" label={Translate.string('Apply changes')} />
        </Form>
      )}
    </FinalForm>
  );
}

TimeEditForm.propTypes = {
  entry: entrySchema.isRequired,
  uses24HourFormat: PropTypes.bool.isRequired,
};

export default function TimeDisplay({entry, uses24HourFormat}) {
  return (
    <Accordion
      panels={[
        {
          key: 'time',
          title: {
            content: (
              <>
                {moment(entry.start).format('HH:mm')} - {moment(entry.end).format('HH:mm')}
                <Icon
                  name="pencil"
                  color="grey"
                  className="right"
                  title={Translate.string('Change time')}
                  link
                />
              </>
            ),
            icon: 'clock outline',
          },
          content: {
            content: <TimeEditForm entry={entry} uses24HourFormat={uses24HourFormat} />,
          },
        },
      ]}
    />
  );
}

TimeDisplay.propTypes = {
  entry: entrySchema.isRequired,
  uses24HourFormat: PropTypes.bool.isRequired,
};
