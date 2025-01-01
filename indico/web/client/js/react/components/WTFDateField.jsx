// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'react-dates/initialize';
import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useEffect, useMemo, useRef, useState, useCallback} from 'react';

import {SingleDatePicker} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {toMoment} from 'indico/utils/date';

function triggerChange(id) {
  document.getElementById(id).dispatchEvent(new Event('change', {bubbles: true}));
}

export default function WTFDateField({
  dateId,
  required,
  disabled,
  allowClear,
  earliest,
  latest,
  linkedField,
}) {
  const dateField = useMemo(() => document.getElementById(dateId), [dateId]);
  const linkedFieldDateElem = useMemo(
    () => linkedField && document.getElementById(`${linkedField.id}-datestorage`),
    [linkedField]
  );
  const [date, setDate] = useState(toMoment(dateField.value, 'DD/MM/YYYY', true));
  const earliestMoment = earliest ? moment(earliest) : null;
  const latestMoment = latest ? moment(latest) : null;
  const clearRef = useRef(null);

  const updateDate = useCallback(
    value => {
      dateField.value = value ? value.format('DD/MM/YYYY') : '';
      setDate(value);
      triggerChange(dateId);
    },
    [dateField, dateId]
  );

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
    updateDate(null);
    clearRef.current.dispatchEvent(new Event('indico:closeAutoTooltip'));
  };

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
        required={required}
        verticalSpacing={10}
        showDefaultInputIcon={false}
        disabled={disabled}
        noBorder
      />
      {date && allowClear && (
        <span
          onClick={clearFields}
          className="clear-pickers"
          title={Translate.string('Clear date')}
          ref={clearRef}
        />
      )}
    </>
  );
}

WTFDateField.propTypes = {
  dateId: PropTypes.string.isRequired,
  required: PropTypes.bool,
  disabled: PropTypes.bool,
  allowClear: PropTypes.bool,
  earliest: PropTypes.string,
  latest: PropTypes.string,
  linkedField: PropTypes.object,
};

WTFDateField.defaultProps = {
  required: false,
  disabled: false,
  allowClear: false,
  earliest: null,
  latest: null,
  linkedField: null,
};
