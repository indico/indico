// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import timeTableURL from 'indico-url:event_registration.api_event_timetable';

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {useSelector} from 'react-redux';
import {Checkbox, Form, Accordion, Icon} from 'semantic-ui-react';

import {
  FinalCheckbox,
  FinalRadio,
  FinalField,
  FinalInput,
  validators as v,
} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate, Param, Plural, PluralTranslate, Singular} from 'indico/react/i18n';

import '../../../styles/regform.module.scss';
import {getStaticData} from '../selectors';

const sessionDataSchema = PropTypes.arrayOf(
  PropTypes.shape({
    fullTitle: PropTypes.string.isRequired,
    id: PropTypes.number.isRequired,
    startDt: PropTypes.string.isRequired,
  })
);

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
  const [expandedHeaders, setExpandedHeaders] = useState([]);

  const markTouched = () => {
    onFocus();
    onBlur();
  };

  function handleValueChange(e, data) {
    markTouched();
    const id = data.value;
    const newValue = _.xor(value, [id]);
    onChange(newValue);
  }

  function handleHeaderClick(e, accordion) {
    if (expandedHeaders.includes(accordion.index)) {
      setExpandedHeaders(expandedHeaders.filter(el => el !== accordion.index));
    } else {
      setExpandedHeaders([...expandedHeaders, accordion.index]);
    }
  }

  useEffect(() => {
    setExpandedHeaders(
      sessionData && display === 'expanded' ? [...Array(_.keys(sessionData).length).keys()] : []
    );
  }, [sessionData, display]);

  return (
    <Form.Group styleName="timetablesessions-field">
      {sessionData &&
        Object.keys(sessionData).map((date, index) => (
          <SessionBlockHeader
            value={value}
            index={index}
            name={name}
            data={sessionData[date]}
            label={moment(date).format('dddd ll')}
            isExpanded={expandedHeaders.includes(index)}
            allowFullDays={allowFullDays}
            key={date}
            handleValueChange={handleValueChange}
            onChange={onChange}
            onClick={handleHeaderClick}
            props={props}
          />
        ))}
    </Form.Group>
  );
}

TimetableSessionsComponent.propTypes = {
  value: PropTypes.arrayOf(PropTypes.number).isRequired,
  name: PropTypes.string.isRequired,
  sessionData: PropTypes.objectOf(sessionDataSchema),
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
  index,
  data,
  label,
  isExpanded,
  allowFullDays,
  handleValueChange,
  onChange,
  onClick,
}) {
  const childrenIds = data.map(e => e.id);
  const isAllChecked = childrenIds.every(id => value.includes(id));
  const isAnyChecked = childrenIds.some(id => value.includes(id));
  const selectedBlocks = value.filter(element => childrenIds.includes(element)).length;

  function handleHeaderChange(e) {
    e.stopPropagation();
    const newValue =
      isAllChecked || isAnyChecked
        ? value.filter(element => !childrenIds.includes(element))
        : [...value, ...childrenIds];
    onChange(newValue);
  }

  return (
    <Accordion styled exclusive={false}>
      <Accordion.Title active={isExpanded} index={index} onClick={onClick}>
        <Icon name="dropdown" />
        <Checkbox
          checked={isAllChecked}
          onChange={handleHeaderChange}
          indeterminate={isAnyChecked && !isAllChecked}
          disabled={!allowFullDays}
          label={label}
        />
        <span>
          <PluralTranslate count={selectedBlocks}>
            <Singular>
              (<Param name="selectedBlocks" value={selectedBlocks} /> block selected)
            </Singular>
            <Plural>
              (<Param name="selectedBlocks" value={selectedBlocks} /> blocks selected)
            </Plural>
          </PluralTranslate>
        </span>
      </Accordion.Title>
      <Accordion.Content active={isExpanded}>
        {data.map(({fullTitle, id}) => (
          <dd className="grouped-fields" key={id}>
            <Checkbox
              value={id}
              onChange={handleValueChange}
              checked={value.includes(id)}
              label={fullTitle}
            />
          </dd>
        ))}
      </Accordion.Content>
    </Accordion>
  );
}

SessionBlockHeader.propTypes = {
  value: PropTypes.arrayOf(PropTypes.number).isRequired,
  index: PropTypes.number.isRequired,
  data: sessionDataSchema.isRequired,
  label: PropTypes.string.isRequired,
  isExpanded: PropTypes.bool.isRequired,
  allowFullDays: PropTypes.bool.isRequired,
  handleValueChange: PropTypes.func.isRequired,
  onChange: PropTypes.func.isRequired,
  onClick: PropTypes.func.isRequired,
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
  const {data: sessionData} = useIndicoAxios(
    {url: timeTableURL({event_id: eventId})},
    {camelize: true}
  );
  let validationMsg;

  if (minimum > 0 && maximum > 0) {
    validationMsg = PluralTranslate.string(
      'Please select at least {minimum} and no more than {maximum} session block',
      'Please select at least {minimum} and no more than {maximum} session blocks',
      maximum,
      {minimum, maximum}
    );
  } else if (minimum > 0) {
    validationMsg = PluralTranslate.string(
      'Please select at least {minimum} session block',
      'Please select at least {minimum} session blocks',
      minimum,
      {minimum}
    );
  } else {
    validationMsg = PluralTranslate.string(
      'Please select no more than {maximum} session block',
      'Please select no more than {maximum} session blocks',
      maximum,
      {maximum}
    );
  }

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
          return validationMsg;
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
        <FinalRadio name="display" label={Translate.string('Expanded dropdown')} value="expanded" />
        <FinalRadio
          name="display"
          label={Translate.string('Collapsed dropdown')}
          value="collapsed"
        />
      </Form.Group>

      <FinalCheckbox name="allowFullDays" label={Translate.string('Allow selecting full days.')} />
      <FinalInput
        name="minimum"
        type="number"
        label={Translate.string('Minimum number of choices')}
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
        label={Translate.string('Maximum number of choices')}
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
