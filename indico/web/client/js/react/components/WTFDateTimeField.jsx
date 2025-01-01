// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'react-dates/initialize';
import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import TimePicker from 'rc-time-picker';
import React, {useEffect, useMemo, useRef, useState, useCallback} from 'react';

import {SingleDatePicker} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {toMoment} from 'indico/utils/date';

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
}) {
  const dateField = useMemo(() => document.getElementById(dateId), [dateId]);
  const timeField = useMemo(() => document.getElementById(timeId), [timeId]);
  const timezoneField = useMemo(() => document.getElementById(timezoneFieldId), [timezoneFieldId]);
  const linkedFieldDateElem = useMemo(
    () => linkedField && document.getElementById(`${linkedField.id}-datestorage`),
    [linkedField]
  );
  const [time, setTime] = useState(toMoment(timeField.value, 'HH:mm', true));
  const [date, setDate] = useState(toMoment(dateField.value, 'DD/MM/YYYY', true));
  const [currentTimezone, setTimezone] = useState(timezone);
  const earliestMoment = earliest ? moment(earliest) : null;
  const latestMoment = latest ? moment(latest) : null;
  const format = uses24HourFormat ? 'H:mm' : 'h:mm a';
  const timePickerRef = useRef(null);
  const clearRef = useRef(null);

  const updateTime = useCallback(
    value => {
      timeField.value = value ? value.format('HH:mm') : '';
      setTime(value);
      triggerChange(timeId);
    },
    [timeField, timeId]
  );

  const updateDate = useCallback(
    value => {
      if (value && timeField.value === '') {
        updateTime(moment(defaultTime, 'HH:mm'));
      }
      dateField.value = value ? value.format('DD/MM/YYYY') : '';
      setDate(value);
      triggerChange(dateId);
      timePickerRef.current.picker.required = value;
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

  useEffect(() => {
    timePickerRef.current.picker.required = required;
  }, [required]);

  useEffect(() => {
    if (!linkedField) {
      return;
    }
    function handleDateChange() {
      const linkedDate = moment(linkedFieldDateElem.value, 'DD/MM/YYYY');
      if (
        (linkedField.notBefore && linkedDate.isAfter(date, 'day')) ||
        (linkedField.notAfter && linkedDate.isBefore(date, 'day'))
      ) {
        updateDate(linkedDate);
      }
    }
    linkedFieldDateElem.addEventListener('change', handleDateChange);

    return () => {
      linkedFieldDateElem.removeEventListener('change', handleDateChange);
    };
  }, [date, linkedFieldDateElem, linkedField, updateDate]);

  const clearFields = () => {
    updateTime(null);
    updateDate(null);
    clearRef.current.dispatchEvent(new Event('indico:closeAutoTooltip'));
  };

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

  const isOutsideRange = useCallback(
    value => {
      if (linkedField) {
        const linkedDate = moment(linkedFieldDateElem.value, 'DD/MM/YYYY');
        if (
          (linkedField.notBefore && value.isBefore(linkedDate, 'day')) ||
          (linkedField.notAfter && value.isAfter(linkedDate, 'day'))
        ) {
          return true;
        }
      }
      return (
        (earliestMoment && value.isBefore(earliestMoment, 'day')) ||
        (latestMoment && value.isAfter(latestMoment, 'day'))
      );
    },
    [earliestMoment, latestMoment, linkedField, linkedFieldDateElem]
  );

  return (
    <>
      <SingleDatePicker
        id=""
        date={date}
        onDateChange={updateDate}
        placeholder={moment.localeData().longDateFormat('L')}
        isOutsideRange={isOutsideRange}
        required={!!time || required}
        verticalSpacing={10}
        showDefaultInputIcon={false}
        disabled={disabled}
        noBorder
      />
      <TimePicker
        showSecond={false}
        value={time}
        focusOnOpen
        format={format}
        onChange={updateTime}
        use12Hours={!uses24HourFormat}
        allowEmpty={false}
        placeholder="--:--"
        disabledHours={getDisabledHours}
        disabledMinutes={getDisabledMinutes}
        disabled={disabled}
        ref={timePickerRef}
        // keep the picker in the DOM tree of the surrounding element to avoid
        // e.g. qbubbles from closing when a picker is used inside one and the
        // user clicks something in the picker
        getPopupContainer={node => node}
      />
      <i className="timezone" id={`${timeId}-timezone`} title={currentTimezone} />
      {(time || date) && allowClear && !disabled && (
        <span
          onClick={clearFields}
          className="clear-pickers"
          title={Translate.string('Clear date and time')}
          ref={clearRef}
        />
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
};

WTFDateTimeField.defaultProps = {
  timezoneFieldId: null,
  required: false,
  disabled: false,
  allowClear: false,
  earliest: null,
  latest: null,
  linkedField: null,
};
