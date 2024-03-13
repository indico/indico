// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import timeTableURL from 'indico-url:event_registration.api_event_timetable';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useSelector} from 'react-redux';
import {Checkbox, Form, Accordion, Icon} from 'semantic-ui-react';

import '../../../../../../rb/client/js/modules/roomList/filters/EquipmentForm.module.scss';

import {
  FinalCheckbox,
  FinalRadio,
  FinalField,
  FinalInput,
  validators as v,
} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate, PluralTranslate} from 'indico/react/i18n';
import {camelizeKeys} from 'indico/utils/case';
import {$T} from 'indico/utils/i18n';

import '../../../styles/regform.module.scss';
import {getStaticData} from '../selectors';

function TimetableSessionsComponent({
  value,
  name,
  sessionData,
  onChange,
  onFocus,
  onBlur,
  allowFullDays,
  display,
  minimum,
  maximum,
  ...props
}) {
  const markTouched = () => {
    onFocus();
    onBlur();
  };

  function handleValueChange(e, data) {
    markTouched();
    const id = data.value;
    const newValue = value.includes(id) ? value.filter(el => el !== id) : [...value, id];
    onChange(newValue);
  }

  function formatDate(date) {
    const options = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      weekday: 'short',
    };
    const dt = new Date(date);
    return dt.toLocaleDateString(undefined, options);
  }

  const currentSelectionMsg = $T.gettext('You selected {0} session blocks.').format(value.length);

  return (
    <Form.Group styleName="timetablesessions-field">
      <strong>{currentSelectionMsg}</strong>
      {sessionData &&
        Object.keys(sessionData)?.map((date, index) => (
          <SessionBlockHeader
            value={value}
            index={index}
            name={name}
            data={sessionData[date]}
            label={formatDate(date)}
            allowFullDays={allowFullDays}
            display={display}
            key={`session-block-${date}`}
            handleValueChange={handleValueChange}
            onChange={onChange}
            props={props}
          />
        ))}
    </Form.Group>
  );
}

TimetableSessionsComponent.propTypes = {
  value: PropTypes.arrayOf(PropTypes.number).isRequired,
  name: PropTypes.string.isRequired,
  sessionData: PropTypes.objectOf(
    PropTypes.arrayOf(
      PropTypes.shape({
        full_title: PropTypes.string.isRequired,
        id: PropTypes.number.isRequired,
        start_dt: PropTypes.string.isRequired,
      })
    )
  ),
  onChange: PropTypes.func.isRequired,
  onFocus: PropTypes.func.isRequired,
  onBlur: PropTypes.func.isRequired,
  allowFullDays: PropTypes.bool.isRequired,
  display: PropTypes.oneOf(['expanded', 'collapsed']),
  maximum: PropTypes.number.isRequired,
  minimum: PropTypes.number.isRequired,
};

TimetableSessionsComponent.defaultProps = {
  sessionData: {},
  display: 'expanded',
};

function SessionBlockHeader({
  value,
  data,
  label,
  allowFullDays,
  display,
  handleValueChange,
  onChange,
}) {
  const childrenIds = data.map(e => e.id);
  const isChecked = childrenIds.reduce((acum, id) => {
    return acum && value.includes(id);
  }, true);
  const isIndeterminate = childrenIds.reduce((acum, id) => {
    return acum || value.includes(id);
  }, false);
  const [isExpanded, setIsExpanded] = useState(display === 'expanded');

  const isExpandedClass = isExpanded ? '' : 'hidden';

  function handleHeaderClick() {
    setIsExpanded(!isExpanded);
  }

  function handleHeaderChange() {
    const newValue =
      isChecked || isIndeterminate
        ? value.filter(element => !childrenIds.includes(element))
        : [...value, ...childrenIds];
    onChange(newValue);
  }

  return (
    <>
      <Accordion styleName="equipment-accordion" className="ui-state-default">
        <Accordion.Title active={isExpanded} index={0} onClick={handleHeaderClick}>
          <Icon name="dropdown" />
          <Checkbox
            checked={isChecked}
            onChange={handleHeaderChange}
            indeterminate={isIndeterminate && !isChecked}
            disabled={!allowFullDays}
            label={label}
          />
        </Accordion.Title>
      </Accordion>
      {data.map(({fullTitle, id}) => (
        <dd className="grouped-fields" key={id}>
          <Checkbox
            value={id}
            onChange={handleValueChange}
            checked={value.includes(id)}
            label={fullTitle}
            className={isExpandedClass}
          />
        </dd>
      ))}
    </>
  );
}

SessionBlockHeader.propTypes = {
  value: PropTypes.arrayOf(PropTypes.number).isRequired,
  data: PropTypes.arrayOf(PropTypes.object).isRequired,
  label: PropTypes.string.isRequired,
  allowFullDays: PropTypes.bool.isRequired,
  display: PropTypes.string.isRequired,
  handleValueChange: PropTypes.func.isRequired,
  onChange: PropTypes.func.isRequired,
};

export default function TimetableSessionsInput({
  htmlId,
  htmlName,
  disabled,
  isRequired,
  allowFullDays,
  display,
  minimum,
  maximum,
}) {
  const {eventId} = useSelector(getStaticData);
  const {data: sessionData} = camelizeKeys(
    useIndicoAxios({url: timeTableURL({event_id: eventId})})
  );

  const minMsg = minimum > 0 ? `at least ${minimum}` : ``;
  const and = minimum > 0 && maximum > 0 ? ` and ` : ``;
  const maxMsg = maximum > 0 ? `no more than ${maximum}` : ``;

  return (
    <FinalField
      id={htmlId}
      name={htmlName}
      component={TimetableSessionsComponent}
      disabled={disabled}
      required={isRequired}
      allowFullDays={allowFullDays}
      display={display}
      minimum={minimum}
      maximum={maximum}
      sessionData={sessionData}
      validate={value => {
        if (value.length < minimum || value.length > maximum) {
          return PluralTranslate.string(
            'Please select {0}{1}{2} session block.',
            'Please select {0}{1}{2} session blocks.',
            maximum,
            {0: minMsg, 1: and, 2: maxMsg}
          );
        }
      }}
    />
  );
}

TimetableSessionsInput.propTypes = {
  htmlId: PropTypes.string.isRequired,
  htmlName: PropTypes.string.isRequired,
  isRequired: PropTypes.bool.isRequired,
  disabled: PropTypes.bool,
  display: PropTypes.string,
  allowFullDays: PropTypes.bool,
  minimum: PropTypes.number,
  maximum: PropTypes.number,
};

TimetableSessionsInput.defaultProps = {
  disabled: false,
  display: 'expanded',
  allowFullDays: false,
  minimum: 0,
  maximum: 0,
};

export function TimetableSessionsSettings() {
  return (
    <>
      <Form.Group inline>
        <label>{Translate.string('Default display for sessions')}</label>
        <FinalRadio name="display" label={Translate.string('Expanded.')} value="expanded" />
        <FinalRadio name="display" label={Translate.string('Collapsed.')} value="collapsed" />
      </Form.Group>

      <FinalCheckbox name="allowFullDays" label={Translate.string('Allow selecting full days.')} />
      <FinalInput
        name="minimum"
        type="number"
        label={Translate.string('Minimum selection')}
        placeholder={String(TimetableSessionsInput.defaultProps.minimum)}
        step="1"
        min="0"
        validate={v.optional(v.min(0))}
        format={val => val || ''}
        parse={val => +val || 0}
        fluid
      />
      <FinalInput
        name="maximum"
        type="number"
        label={Translate.string('Maximum selection')}
        placeholder={Translate.string('No Maximum')}
        step="1"
        min="0"
        validate={v.optional(v.min(0))}
        format={val => val || ''}
        parse={val => +val || 0}
        fluid
      />
    </>
  );
}

export const timetableSessionsSettingsInitialData = {
  display: 'expanded',
  allowFullDays: false,
  minimum: 0,
  maximum: 0,
};
