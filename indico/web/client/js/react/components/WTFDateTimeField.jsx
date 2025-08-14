// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useEffect, useMemo, useRef, useState, useCallback} from 'react';

import {DatePicker, TimePicker} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {serializeDate, toMoment} from 'indico/utils/date';
import {formatDate, ISO_FORMAT} from 'indico/utils/date_format';

import {INVALID} from './DatePicker';

function triggerChange(id) {
  document.getElementById(id).dispatchEvent(new Event('change', {bubbles: true}));
}

export default function WTFDateTimeField({
  timeId,
  dateId,
  timezoneFieldId,
  timezone,
  uses24HourFormat,
  required,
  disabled,
  allowClear,
  earliest,
  latest,
  defaultTime,
  linkedField,
  disabledDays,
  disabledDates,
}) {
  // The hidden field that holds the date (in isoformat) which is used during form submission.
  // It also contains the initial value coming from the WTForms field.
  const dateField = useMemo(() => document.getElementById(dateId), [dateId]);
  const timeField = useMemo(() => document.getElementById(timeId), [timeId]);
  const timezoneField = useMemo(() => document.getElementById(timezoneFieldId), [timezoneFieldId]);
  // The hidden field containing the linked field's date.
  const linkedFieldDateElem = useMemo(
    () => linkedField && document.getElementById(`${linkedField.id}-datestorage`),
    [linkedField]
  );
  // The moment object of the linked field's date.
  const [linkedMoment, setLinkedMoment] = useState(
    linkedFieldDateElem ? toMoment(linkedFieldDateElem.value, moment.HTML5_FMT.DATE) : null
  );
  // The currently selected valid date, or null if there isn't one.
  const [date, setDate] = useState(
    dateField.value ? toMoment(dateField.value, moment.HTML5_FMT.DATE) : null
  );
  const [time, setTime] = useState(toMoment(timeField.value, 'HH:mm', true));
  const [currentTimezone, setTimezone] = useState(timezone);
  const earliestMoment = earliest ? moment(earliest) : null;
  const latestMoment = latest ? moment(latest) : null;
  // const timePickerRef = useRef(null);
  const clearRef = useRef(null);

  const updateTime = useCallback(
    value => {
      const momentValue = value ? toMoment(value, 'HH:mm', true) : null;
      timeField.value = momentValue?.format('HH:mm') ?? '';
      setTime(momentValue);
      triggerChange(timeId);
    },
    [timeField, timeId]
  );

  const filter = d => {
    const dateStr = formatDate(ISO_FORMAT, d);
    if (disabledDates?.includes(dateStr)) {
      return false;
    }
    return !(disabledDays && disabledDays.includes(d.getDay()));
  };

  const updateDate = useCallback(
    (value, updatePicker = false) => {
      const picker = dateField.parentElement.querySelector('ind-date-picker');
      const pickerInput = picker.querySelector('input');
      if (value === INVALID) {
        // this typically happens when the user types something in the field that's not a
        // valid date (yet)
        dateField.value = '';
        pickerInput.setCustomValidity(Translate.string('The entered date is invalid.'));
        setDate(null);
        // timePickerRef.current.picker.required = false;
      } else {
        if (value && timeField.value === '') {
          updateTime(moment(defaultTime, 'HH:mm'));
        }
        dateField.value = value || '';
        if (updatePicker) {
          // update the date picker's input, if the change was done programmatically, e.g. via
          // the clear button or linked fields
          picker.value = value ? serializeDate(toMoment(value, moment.HTML5_FMT.DATE)) : '';
        }
        pickerInput.setCustomValidity('');
        setDate(value ? toMoment(value, moment.HTML5_FMT.DATE) : null);
        // timePickerRef.current.picker.required = !!value;
      }
      triggerChange(dateId);
    },
    [dateField, timeField, dateId, defaultTime, updateTime]
  );

  useEffect(() => {
    if (!timezoneField) {
      return;
    }
    function handleTimezone() {
      setTimezone(timezoneField.value);
    }
    timezoneField.addEventListener('change', handleTimezone);

    return () => {
      timezoneField.removeEventListener('change', handleTimezone);
    };
  }, [timezoneField]);

  // useEffect(() => {
  //   timePickerRef.current.picker.required = required;
  // }, [required]);

  useEffect(() => {
    if (!linkedField) {
      return;
    }
    function handleDateChange() {
      const linkedDate = toMoment(linkedFieldDateElem.value, moment.HTML5_FMT.DATE);
      setLinkedMoment(linkedDate);
      if (
        (linkedField.notBefore && linkedDate?.isAfter(date, 'day')) ||
        (linkedField.notAfter && linkedDate?.isBefore(date, 'day'))
      ) {
        updateDate(serializeDate(linkedDate), true);
      }
    }
    linkedFieldDateElem.addEventListener('change', handleDateChange);

    return () => {
      linkedFieldDateElem.removeEventListener('change', handleDateChange);
    };
  }, [date, linkedFieldDateElem, linkedField, updateDate]);

  const clearFields = () => {
    updateTime(null);
    updateDate(null, true);
    clearRef.current.dispatchEvent(new Event('indico:closeAutoTooltip'));
  };

  // TODO pass min/max time instaed once the time picker supports it
  const getDisabledHours = useCallback(() => {
    const hours = [];
    if ((earliestMoment || latestMoment) && !date) {
      return _.range(24);
    }
    if (earliestMoment && date.isSame(earliestMoment, 'day')) {
      hours.push(_.range(earliestMoment.hour()));
    }
    if (latestMoment && date.isSame(latestMoment, 'day')) {
      const hour = latestMoment.hour();
      hours.push([...Array(23 - hour).keys()].map(x => x + hour + 1));
    }
    return _.flatten(hours);
  }, [earliestMoment, latestMoment, date]);

  const getDisabledMinutes = useCallback(
    h => {
      if ((earliestMoment || latestMoment) && !date) {
        return _.range(60);
      }
      const minutes = [];
      if (earliestMoment && date.isSame(earliestMoment, 'day') && h === earliestMoment.hour()) {
        minutes.push(_.range(earliestMoment.minutes()));
      }
      if (latestMoment && date.isSame(latestMoment, 'day') && h === latestMoment.hour()) {
        const minute = latestMoment.minutes();
        minutes.push([...Array(59 - minute).keys()].map(x => x + minute + 1));
      }
      return _.flatten(minutes);
    },
    [earliestMoment, latestMoment, date]
  );

  const min =
    linkedField?.notBefore && linkedMoment
      ? serializeDate(linkedMoment)
      : serializeDate(toMoment(earliest));
  const max =
    linkedField?.notAfter && linkedMoment
      ? serializeDate(linkedMoment)
      : serializeDate(toMoment(latest));

  return (
    <>
      <DatePicker
        value={serializeDate(date)}
        onChange={updateDate}
        min={min}
        max={max}
        filter={filter}
        required={!!time || required}
        disabled={disabled}
      />
      <TimePicker
        value="13:37"
        timeFormat={uses24HourFormat ? '24h' : '12h'}
        onChange={updateTime}
        // disabledHours={getDisabledHours}
        // disabledMinutes={getDisabledMinutes}
        disabled={disabled}
        // ref={timePickerRef}
        required={!!date || required}
        // keep the picker in the DOM tree of the surrounding element to avoid
        // e.g. qbubbles from closing when a picker is used inside one and the
        // user clicks something in the picker
        // getPopupContainer={node => node}
      />
      <i className="timezone" id={`${timeId}-timezone`} title={currentTimezone} />
      {(time || date) && allowClear && !disabled && (
        <button type="button" onClick={clearFields} className="clear-pickers" ref={clearRef}>
          <Translate as="span">Clear date and time</Translate>
        </button>
      )}
    </>
  );
}

WTFDateTimeField.propTypes = {
  timeId: PropTypes.string.isRequired,
  dateId: PropTypes.string.isRequired,
  timezoneFieldId: PropTypes.string,
  timezone: PropTypes.string.isRequired,
  uses24HourFormat: PropTypes.bool.isRequired,
  required: PropTypes.bool,
  disabled: PropTypes.bool,
  allowClear: PropTypes.bool,
  earliest: PropTypes.string,
  latest: PropTypes.string,
  defaultTime: PropTypes.string.isRequired,
  linkedField: PropTypes.object,
  disabledDays: PropTypes.arrayOf(PropTypes.oneOf([0, 1, 2, 3, 4, 5, 6])),
  disabledDates: PropTypes.arrayOf(PropTypes.string),
};

WTFDateTimeField.defaultProps = {
  timezoneFieldId: null,
  required: false,
  disabled: false,
  allowClear: false,
  earliest: null,
  latest: null,
  linkedField: null,
  disabledDays: null,
  disabledDates: null,
};
