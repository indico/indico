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

import {INVALID} from './DatePicker';

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
  // The hidden field that holds the date (in isoformat) which is used during form submission.
  // It also contains the initial value coming from the WTForms field.
  const dateField = useMemo(() => document.getElementById(dateId), [dateId]);
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
  const clearRef = useRef(null);

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
      } else {
        dateField.value = value || '';
        if (updatePicker) {
          // update the date picker's input, if the change was done programmatically, e.g. via
          // the clear button or linked fields
          picker.value = value ? serializeDate(toMoment(value, moment.HTML5_FMT.DATE)) : '';
        }
        pickerInput.setCustomValidity('');
        setDate(value ? toMoment(value, moment.HTML5_FMT.DATE) : null);
      }
      triggerChange(dateId);
    },
    [dateField, dateId]
  );

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
    updateDate(null, true);
    clearRef.current.dispatchEvent(new Event('indico:closeAutoTooltip'));
  };

  const min = linkedField?.notBefore && linkedMoment ? serializeDate(linkedMoment) : earliest;
  const max = linkedField?.notAfter && linkedMoment ? serializeDate(linkedMoment) : latest;

  return (
    <>
      <DatePicker
        value={serializeDate(date)}
        onChange={updateDate}
        min={min}
        max={max}
        required={required}
        disabled={disabled}
      />
      {date && allowClear && (
        <button type="button" onClick={clearFields} className="clear-pickers" ref={clearRef}>
          <Translate as="span">Clear date</Translate>
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
