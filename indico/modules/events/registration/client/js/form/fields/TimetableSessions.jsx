// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import sessionBlocksURL from 'indico-url:event_registration.api_session_blocks';

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useEffect, useMemo, useState} from 'react';
import {useSelector} from 'react-redux';
import {Form, Accordion, AccordionTitle, AccordionContent, Icon} from 'semantic-ui-react';

import {Checkbox} from 'indico/react/components';
import {FinalCheckbox, FinalField, FinalInput, validators as v} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate, Param, Plural, PluralTranslate, Singular} from 'indico/react/i18n';

import {getManagement} from '../../form_submission/selectors';
import {getStaticData} from '../selectors';

import '../../../styles/regform.module.scss';

import './TimetableSessions.module.scss';

const sessionDataSchema = PropTypes.arrayOf(
  PropTypes.shape({
    id: PropTypes.number.isRequired,
    fullTitle: PropTypes.string.isRequired,
    time: PropTypes.string.isRequired,
  })
);

function TimetableSessionsComponent({
  value,
  name,
  sessionData,
  onChange: _onChange,
  onFocus,
  onBlur,
  collapseDays,
  minimum,
  maximum,
  ...props
}) {
  const [expandedHeaders, setExpandedHeaders] = useState({});

  useEffect(() => {
    setExpandedHeaders(
      Object.fromEntries(Object.keys(sessionData || {}).map(date => [date, !collapseDays]))
    );
  }, [sessionData, collapseDays]);

  const validBlockIds = useMemo(() => {
    if (!sessionData) {
      return [];
    }
    return new Set(
      Object.values(sessionData)
        .flat()
        .map(x => x.id)
    );
  }, [sessionData]);

  const markTouched = () => {
    onFocus();
    onBlur();
  };

  const onChange = val => {
    // remove any invalid IDs (deleted session blocks)
    _onChange(val.filter(x => validBlockIds.has(x)));
  };

  const handleValueChange = evt => {
    markTouched();
    const id = Number(evt.target.value);
    const newValue = _.xor(value, [id]);
    onChange(newValue);
  };

  const handleHeaderClick = date => evt => {
    if (evt.target.closest('label')) {
      // Interacted with the checkbox, don't toggle
      return;
    }
    setExpandedHeaders({...expandedHeaders, [date]: !expandedHeaders[date]});
  };

  return (
    <Form.Group styleName="timetablesessions-field">
      <Accordion styled exclusive={false}>
        {sessionData &&
          Object.keys(sessionData).map((date, index) => (
            <SessionBlockHeader
              value={value}
              index={index}
              name={name}
              data={sessionData[date]}
              label={moment(date).format('dddd ll')}
              isExpanded={expandedHeaders[date] ?? false}
              key={date}
              handleValueChange={handleValueChange}
              onChange={onChange}
              onClick={handleHeaderClick(date)}
              props={props}
            />
          ))}
      </Accordion>
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
  collapseDays: PropTypes.bool.isRequired,
  maximum: PropTypes.number.isRequired,
  minimum: PropTypes.number.isRequired,
};

TimetableSessionsComponent.defaultProps = {
  sessionData: {},
};

function SessionBlockHeader({
  value,
  index,
  data,
  label,
  isExpanded,
  handleValueChange,
  onChange,
  onClick,
}) {
  const childrenIds = data.map(x => x.id);
  const isAllChecked = childrenIds.every(id => value.includes(id));
  const isAnyChecked = childrenIds.some(id => value.includes(id));
  const selectedBlocks = value.filter(element => childrenIds.includes(element)).length;

  function handleHeaderChange(evt) {
    evt.stopPropagation();
    const newValue =
      isAllChecked || isAnyChecked
        ? value.filter(element => !childrenIds.includes(element))
        : [...value, ...childrenIds];
    onChange(newValue);
  }

  return (
    <>
      <AccordionTitle
        styleName="accordion-title"
        active={isExpanded}
        index={index}
        onClick={onClick}
      >
        <Icon name="dropdown" />
        <Checkbox
          styleName="accordion-title-checkbox"
          checked={isAllChecked}
          onChange={handleHeaderChange}
          indeterminate={isAnyChecked && !isAllChecked}
          label={label}
        />
        <span styleName="selection-count">
          (
          <PluralTranslate count={selectedBlocks}>
            <Singular>
              <Param name="selectedBlocks" value={selectedBlocks} /> block selected)
            </Singular>
            <Plural>
              <Param name="selectedBlocks" value={selectedBlocks} /> blocks selected)
            </Plural>
          </PluralTranslate>
        </span>
      </AccordionTitle>
      <AccordionContent as="ul" active={isExpanded}>
        {data.map(({time, fullTitle, id}) => (
          <li styleName="session-block" className="grouped-fields" key={id}>
            <Checkbox
              value={id}
              onChange={handleValueChange}
              checked={value.includes(id)}
              label={`${time} - ${fullTitle}`}
            />
          </li>
        ))}
      </AccordionContent>
    </>
  );
}

SessionBlockHeader.propTypes = {
  value: PropTypes.arrayOf(PropTypes.number).isRequired,
  index: PropTypes.number.isRequired,
  data: sessionDataSchema.isRequired,
  label: PropTypes.string.isRequired,
  isExpanded: PropTypes.bool.isRequired,
  handleValueChange: PropTypes.func.isRequired,
  onChange: PropTypes.func.isRequired,
  onClick: PropTypes.func.isRequired,
};

export default function TimetableSessionsInput({
  htmlId,
  htmlName,
  disabled,
  isRequired,
  collapseDays,
  minimum,
  maximum,
}) {
  const {eventId} = useSelector(getStaticData);
  const management = useSelector(getManagement);
  const {data: sessionData} = useIndicoAxios(
    {url: sessionBlocksURL({event_id: eventId, force_event_tz: management})},
    {camelize: true}
  );

  const minMsg = PluralTranslate.string(
    'Please select at least {minimum} session block',
    'Please select at least {minimum} session blocks',
    minimum,
    {minimum}
  );
  const maxMsg = PluralTranslate.string(
    'Please select no more than {maximum} session block',
    'Please select no more than {maximum} session blocks',
    maximum,
    {maximum}
  );

  return (
    <FinalField
      id={htmlId}
      name={htmlName}
      component={TimetableSessionsComponent}
      disabled={disabled}
      required={isRequired}
      collapseDays={collapseDays}
      minimum={minimum}
      maximum={maximum}
      sessionData={sessionData}
      validate={value => {
        if (minimum !== 0 && value.length < minimum) {
          return minMsg;
        } else if (maximum !== 0 && value.length > maximum) {
          return maxMsg;
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
  collapseDays: PropTypes.bool,
  minimum: PropTypes.number,
  maximum: PropTypes.number,
};

TimetableSessionsInput.defaultProps = {
  disabled: false,
  collapseDays: false,
  minimum: 0,
  maximum: 0,
};

export function TimetableSessionsSettings() {
  return (
    <>
      <FinalCheckbox name="collapseDays" label={Translate.string('Collapse days')} showAsToggle />
      <FinalInput
        name="minimum"
        type="number"
        label={Translate.string('Minimum number of choices')}
        placeholder={Translate.string('No minimum')}
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
        placeholder={Translate.string('No maximum')}
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
  collapse_days: false,
  minimum: 0,
  maximum: 0,
};

export function sessionsSettingsFormValidator({minimum, maximum}) {
  if (minimum && maximum && minimum > maximum) {
    const msg = Translate.string('The minimum value cannot be greater than the maximum value.');
    return {
      minimum: msg,
      maximum: msg,
    };
  }
}
