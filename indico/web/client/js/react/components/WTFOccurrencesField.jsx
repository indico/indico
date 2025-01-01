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

import {SingleDatePicker} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

function triggerChange(field) {
  field.dispatchEvent(new Event('change', {bubbles: true}));
}

export default function WTFOccurrencesField({fieldId, uses24HourFormat}) {
  const field = useMemo(() => document.getElementById(fieldId), [fieldId]);
  const [values, setValues] = useState(() =>
    JSON.parse(field.value).map(value => ({
      date: moment(value.date, 'YYYY-MM-DD'),
      duration: value.duration,
      time: moment(value.time, 'HH:mm'),
      id: _.uniqueId(),
    }))
  );

  const updateOccurrences = newValues => {
    setValues(newValues);
    const storageValues = newValues.map(value => ({
      date: value.date ? value.date.format('YYYY-MM-DD') : '',
      duration: value.duration,
      time: value.time ? value.time.format('HH:mm') : '',
    }));
    field.value = JSON.stringify(storageValues);
  };

  const addOccurrence = () => {
    const lastElement = values[values.length - 1];
    const newValues = [
      ...values,
      {
        date: lastElement.date ? moment(lastElement.date).add(1, 'day') : null,
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
    changeOccurrence(value, occurrence.duration, occurrence.time);
  };

  const updateTime = value => {
    changeOccurrence(occurrence.date, occurrence.duration, value);
  };

  const updateDuration = event => {
    changeOccurrence(occurrence.date, parseInt(event.target.value, 10), occurrence.time);
  };

  return (
    <>
      <SingleDatePicker
        id=""
        date={occurrence.date}
        onDateChange={updateDate}
        placeholder={moment.localeData().longDateFormat('L')}
        verticalSpacing={10}
        showDefaultInputIcon={false}
        isOutsideRange={() => false}
        noBorder
        required
      />
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
      <input
        type="number"
        className="durationpicker"
        value={Number.isNaN(occurrence.duration) ? '' : occurrence.duration}
        onChange={updateDuration}
        step="1"
        min="1"
        required
      />
      <i className="duration-info" title={Translate.string('Duration in minutes')} />
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
