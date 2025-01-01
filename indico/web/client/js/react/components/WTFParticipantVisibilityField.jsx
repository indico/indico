// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useMemo, useState, useEffect} from 'react';
import {Dropdown, Form, Icon, Input, Message} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

export default function WTFParticipantVisibilityField({
  fieldId,
  wrapperId,
  values,
  choices,
  maxVisibilityPeriod,
}) {
  const parentElement = useMemo(() => document.getElementById(wrapperId), [wrapperId]);
  const [participantVisibility, setParticipantVisibility] = useState(values[0]);
  const [publicVisibility, setPublicVisibility] = useState(values[1]);
  const [visibilityDuration, setVisibilityDuration] = useState(values[2]);

  // Trigger change only after the DOM has changed
  useEffect(() => {
    parentElement.dispatchEvent(new Event('change', {bubbles: true}));
  }, [participantVisibility, publicVisibility, visibilityDuration, parentElement]);

  const choiceMap = {
    hide_all: ['hide_all'],
    show_with_consent: ['hide_all', 'show_with_consent'],
    show_all: ['hide_all', 'show_with_consent', 'show_all'],
  };

  const participantOptions = choices.map(([id, title]) => ({
    key: id,
    text: title,
    value: id,
  }));

  const getPublicOptions = value =>
    choices
      .filter(([id]) => choiceMap[value].includes(id))
      .map(([id, title]) => ({
        key: id,
        text: title,
        value: id,
      }));

  const publicOptions = getPublicOptions(participantVisibility);

  return (
    <div>
      <div style={{display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '10px'}}>
        <Form.Field style={{flex: '1 49%'}}>
          <label>
            <Translate>Visibility to participants</Translate>
          </label>
          <Dropdown
            fluid
            onChange={(e, {value}) => {
              setParticipantVisibility(value);

              if (!choiceMap[value].includes(publicVisibility)) {
                const options = getPublicOptions(value);
                setPublicVisibility(options[options.length - 1].value);
              }
            }}
            options={participantOptions}
            selection
            value={participantVisibility}
          />
        </Form.Field>
        <Form.Field style={{flex: '1 49%'}}>
          <label>
            <Translate>Visibility to everyone</Translate>
          </label>
          <Dropdown
            disabled={participantVisibility === 'hide_all'}
            fluid
            onChange={(e, {value}) => {
              setPublicVisibility(value);
            }}
            options={publicOptions}
            selection
            value={publicVisibility}
          />
        </Form.Field>
        <Form.Field style={{flexGrow: 1}}>
          <label>
            <Translate>Visibility duration (weeks)</Translate>
          </label>
          <Input
            type="number"
            placeholder={Translate.string('Permanent')}
            step="1"
            min="1"
            max={maxVisibilityPeriod}
            value={visibilityDuration === null ? '' : visibilityDuration}
            onChange={(evt, {value}) => setVisibilityDuration(value === '' ? null : +value)}
            disabled={participantVisibility === 'hide_all'}
            fluid
          />
        </Form.Field>
      </div>
      {publicVisibility === 'show_all' && (
        <div style={{marginTop: 5}}>
          <Message icon warning>
            <Icon name="warning" />
            <Message.Content>
              <Translate>
                Setting 'Visibility to everyone' to 'Show all participants' is discouraged as
                everyone who can access this event can see the participant list regardless of the
                participants' consent.
              </Translate>
            </Message.Content>
          </Message>
        </div>
      )}
      <input
        type="hidden"
        id={fieldId}
        name={fieldId}
        value={JSON.stringify([participantVisibility, publicVisibility, visibilityDuration])}
      />
    </div>
  );
}

WTFParticipantVisibilityField.propTypes = {
  fieldId: PropTypes.string.isRequired,
  wrapperId: PropTypes.string.isRequired,
  values: PropTypes.array.isRequired,
  choices: PropTypes.array.isRequired,
  maxVisibilityPeriod: PropTypes.number.isRequired,
};
