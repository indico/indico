// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useEffect, useMemo, useRef, useState, useCallback} from 'react';

import {DatePicker} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {serializeDate, toMoment} from 'indico/utils/date';

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
  const [linkedMoment, setLinkedMoment] = useState(
    linkedFieldDateElem ? moment(linkedFieldDateElem.value, 'DD/MM/YYYY') : null
  );
  const [date, setDate] = useState(toMoment(dateField.value, 'DD/MM/YYYY'));
  const clearRef = useRef(null);

  const updateDate = useCallback(
    value => {
      dateField.value = value ? moment(value).format('DD/MM/YYYY') : '';
      dateField.parentElement.querySelector('ind-date-picker > input').value = dateField.value;
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
      setLinkedMoment(linkedDate);
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

  const min =
    linkedField?.notBefore && linkedMoment.isValid() ? serializeDate(linkedMoment) : earliest;
  const max =
    linkedField?.notAfter && linkedMoment.isValid() ? serializeDate(linkedMoment) : latest;

  return (
    <>
      <DatePicker
        value={serializeDate(date)}
        onChange={updateDate}
        min={min}
        max={max}
        required={required}
        disabled={disabled}
        invalidValue={null}
      />
      {date && allowClear && (
        <button type="button" onClick={clearFields} className="clear-pickers" ref={clearRef}>
          <span>{Translate.string('Clear date')}</span>
        </button>
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
