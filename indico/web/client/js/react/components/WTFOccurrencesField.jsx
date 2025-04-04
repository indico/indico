// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import TimePicker from 'rc-time-picker';
import React, {useState, useEffect, useMemo, useRef} from 'react';

import {DatePicker} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

function triggerChange(field) {
  field.dispatchEvent(new Event('change', {bubbles: true}));
}

export default function WTFOccurrencesField({fieldId, uses24HourFormat}) {
  const field = useMemo(() => document.getElementById(fieldId), [fieldId]);
  const [values, setValues] = useState(() =>
    JSON.parse(field.value).map(value => ({
      date: moment(value.date, moment.HTML5_FMT.DATE),
      duration: value.duration,
      time: moment(value.time, 'HH:mm'),
      id: _.uniqueId(),
    }))
  );

  useEffect(() => {
    // we cannot do this directly in updateOccurrences since after adding a new occurrence it
    // doesn't exist in the DOM yet
    const dateInputs = field.parentElement.querySelectorAll('ind-date-picker > input');
    values.forEach(({date}, i) => {
      // time and duration don't allow entering invalid data without the field being in an invalid
      // state, so no need for custom validation there
      dateInputs[i].setCustomValidity(
        date?.isValid() ? '' : Translate.string('The entered date is invalid.')
      );
    });
  }, [field, values]);

  const updateOccurrences = newValues => {
    setValues(newValues);
    const storageValues = newValues.map(value => ({
      date: value.date?.isValid() ? value.date.format(moment.HTML5_FMT.DATE) : '',
      duration: value.duration,
      time: value.time?.isValid() ? value.time.format('HH:mm') : '',
    }));
    field.value = JSON.stringify(storageValues);
  };

  const addOccurrence = () => {
    const lastElement = values[values.length - 1];
    const newValues = [
      ...values,
      {
        date: lastElement.date?.isValid()
          ? moment(lastElement.date, moment.HTML5_FMT.DATE).add(1, 'day')
          : null,
        duration: lastElement.duration,
        time: lastElement.time,
        id: _.uniqueId(),
      },
    ];
    updateOccurrences(newValues);
    triggerChange(field);
  };

  const changeOccurrence = (index, date, duration, time) => {
    const newValues = [...values];
    newValues[index] = {date, duration, time, id: values[index].id};
    updateOccurrences(newValues);
    triggerChange(field);
  };

  const removeOccurrence = index => {
    updateOccurrences(values.filter((__, i) => index !== i));
    triggerChange(field);
  };

  return (
    <>
      {values.map((element, i) => (
        <div className="occurrence" key={element.id}>
          <Occurrence
            occurrence={element}
            uses24HourFormat={uses24HourFormat}
            changeOccurrence={changeOccurrence.bind(null, i)}
            removeOccurrence={values.length > 1 ? removeOccurrence.bind(null, i) : null}
          />
        </div>
      ))}
      <div className="add-occurrence" onClick={addOccurrence}>
        {Translate.string('Add occurrence')}
      </div>
    </>
  );
}

WTFOccurrencesField.propTypes = {
  fieldId: PropTypes.string.isRequired,
  uses24HourFormat: PropTypes.bool.isRequired,
};

function Occurrence({occurrence, uses24HourFormat, changeOccurrence, removeOccurrence}) {
  const format = uses24HourFormat ? 'HH:mm' : 'hh:mm a';
  const clearRef = useRef(null);
  const timePickerRef = useRef(null);

  useEffect(() => {
    timePickerRef.current.picker.required = true;
  }, []);

  const updateDate = value => {
    changeOccurrence(moment(value, moment.HTML5_FMT.DATE), occurrence.duration, occurrence.time);
  };

  const updateTime = value => {
    changeOccurrence(occurrence.date, occurrence.duration, value);
  };

  const updateDuration = event => {
    changeOccurrence(occurrence.date, parseInt(event.target.value, 10), occurrence.time);
  };

  return (
    <>
      <DatePicker value={serializeDate(occurrence.date)} onChange={updateDate} required />
      <TimePicker
        showSecond={false}
        value={occurrence.time}
        format={format}
        onChange={updateTime}
        use12Hours={!uses24HourFormat}
        allowEmpty={false}
        placeholder="--:--"
        ref={timePickerRef}
        // keep the picker in the DOM tree of the surrounding element
        getPopupContainer={node => node}
      />
      <span className="durationpicker">
        <input
          type="number"
          value={Number.isNaN(occurrence.duration) ? '' : occurrence.duration}
          onChange={updateDuration}
          step="1"
          min="1"
          required
        />
        <i className="duration-info" title={Translate.string('Duration in minutes')} />
      </span>
      {removeOccurrence && (
        <span
          className="icon-remove remove-occurrence"
          title={Translate.string('Remove occurrence')}
          onClick={() => {
            clearRef.current.dispatchEvent(new Event('indico:closeAutoTooltip'));
            removeOccurrence();
          }}
          ref={clearRef}
        />
      )}
    </>
  );
}

Occurrence.propTypes = {
  occurrence: PropTypes.shape({
    date: PropTypes.object,
    duration: PropTypes.number,
    time: PropTypes.object,
    id: PropTypes.string,
  }).isRequired,
  uses24HourFormat: PropTypes.bool.isRequired,
  changeOccurrence: PropTypes.func.isRequired,
  removeOccurrence: PropTypes.func,
};

Occurrence.defaultProps = {
  removeOccurrence: null,
};
