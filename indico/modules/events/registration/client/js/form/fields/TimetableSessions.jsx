// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import timeTableURL from 'indico-url:event_registration.api_event_timetable';

import PropTypes from 'prop-types';
import React, {useState, useEffect} from 'react';
import {useSelector} from 'react-redux';
import {Checkbox, Form} from 'semantic-ui-react';

import {
  FinalCheckbox,
  FinalRadio,
  FinalField,
  FinalInput,
  validators as v,
} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

import '../../../styles/regform.module.scss';
import {getStaticData} from '../selectors';

function TimetableSessionsComponent({
  value,
  name,
  sessionData,
  onChange,
  allowFullDays,
  display,
  ...props
}) {
  function handleValueChange(e, data) {
    const id = data.value;
    const newValue = value.includes(id) ? value.filter(el => el !== id) : [...value, id];
    onChange(newValue);
  }

  return (
    <Form.Group styleName="timetablesessions-field">
      {sessionData &&
        Object.keys(sessionData)?.map((date, index) => (
          <SessionBlockHeader
            value={value}
            index={index}
            name={name}
            data={sessionData[date]}
            label={date}
            allowFullDays={allowFullDays}
            display={display}
            key={`session-block-${index}`}
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
  sessionData: PropTypes.object,
  onChange: PropTypes.func.isRequired,
  allowFullDays: PropTypes.bool.isRequired,
  display: PropTypes.string.isRequired,
};

TimetableSessionsComponent.defaultProps = {
  sessionData: {},
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
  const [isChecked, setIsChecked] = useState(false);
  const [isIndeterminate, setIsIndeterminate] = useState(false);
  const [isExpanded, setIsExpanded] = useState(display === 'expanded');

  const arrowLabel = isExpanded ? '▼' : '▶';
  const isExpandedClass = isExpanded ? '' : 'hidden';
  const childrenIds = data.map(e => e.id);

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

  useEffect(() => {
    setIsChecked(() =>
      childrenIds.reduce((acum, id) => {
        return acum && value.includes(id);
      }, true)
    );
    setIsIndeterminate(() =>
      childrenIds.reduce((acum, id) => {
        return acum || value.includes(id);
      }, false)
    );
  }, [value]);

  return (
    <dl>
      <h3 className="ui-state-default">
        <button onClick={handleHeaderClick} className="arrow" type="button">
          {arrowLabel}
        </button>
        <Checkbox
          checked={isChecked}
          onChange={handleHeaderChange}
          indeterminate={isIndeterminate && !isChecked}
          disabled={!allowFullDays}
          label={`${label}`}
        />
      </h3>
      {data?.map(({fullTitle, id}) => (
        <dd className="grouped-fields" key={`session-block-checkbox-${id}`}>
          <Checkbox
            value={id}
            onChange={handleValueChange}
            checked={value.includes(id)}
            label={fullTitle}
            className={isExpandedClass}
          />
        </dd>
      ))}
    </dl>
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
}) {
  const {eventId} = useSelector(getStaticData);
  const {data: sessionData} = useIndicoAxios({url: timeTableURL({event_id: eventId})});

  return (
    <FinalField
      id={htmlId}
      name={htmlName}
      component={TimetableSessionsComponent}
      required={isRequired}
      disabled={disabled}
      display={display}
      allowFullDays={allowFullDays}
      sessionData={sessionData}
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
};

TimetableSessionsInput.defaultProps = {
  disabled: false,
  display: 'expanded',
  allowFullDays: false,
};

export function TimetableSessionsSettings() {
  return (
    <Form id="timetable-sessions-form">
      <Form.Group inline>
        <label>Default display for sessions</label>
        <FinalRadio name="display" label={Translate.string('Expanded.')} value="expanded" />
        <FinalRadio name="display" label={Translate.string('Collapsed.')} value="collapsed" />
      </Form.Group>

      <FinalCheckbox name="allowFullDays" label={Translate.string('Allow selecting full days.')} />
      <FinalInput
        name="minimum"
        type="number"
        label={Translate.string('Minimum selection')}
        placeholder={Translate.string('0')}
        step="1"
        min="0"
        validate={v.optional(v.min(0))}
      />
      <FinalInput
        name="maximum"
        type="number"
        label={Translate.string('Maximum selection')}
        placeholder={Translate.string('0')}
        step="1"
        min="0"
        validate={v.optional(v.min(0))}
      />
    </Form>
  );
}

export const timetableSessionsSettingsInitialData = {
  display: 'expanded',
  allowFullDays: false,
  minimum: 0,
  maximum: 0,
};
