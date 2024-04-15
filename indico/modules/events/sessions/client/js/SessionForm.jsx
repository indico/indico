// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import {Button} from 'semantic-ui-react';

import {FinalLocationField, FinalSessionColorPicker} from 'indico/react/components';
import {FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalDropdown, FinalTimePicker} from 'indico/react/forms/fields';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';

export default function SessionForm() {
  const [modalOpen, setModalOpen] = useState(false);
  // TODO get this from session:
  const eventType = 'conference';
  const sessionTypes = [{text: Translate.string('Poster'), value: 'poster'}];

  return (
    <>
      <Button onClick={() => setModalOpen(true)}>Open Session Form</Button>
      {modalOpen && (
        <FinalModalForm
          id="session-form"
          header={Translate.string('Edit session ???')}
          onSubmit={() => {}}
          onClose={() => setModalOpen(false)}
          initialValues={{location_data: {use_default: true}, colors: {}}}
        >
          <FinalInput name="title" label={Translate.string('Title')} autoFocus required />
          {eventType === 'conference' && (
            <FinalInput
              name="code"
              label={Translate.string('Session code')}
              description={Translate.string(
                'The code that will identify the session in the Book of Abstracts.'
              )}
            />
          )}
          <FinalTextArea name="description" label={Translate.string('Description')} />
          <FinalTimePicker
            name="default_contribution_duration"
            label={Translate.string('Default contribution duration')}
            description={Translate.string(
              'Duration that a contribution created within this session will have by default.'
            )}
            required
          />
          {eventType === 'conference' && sessionTypes.length > 0 && (
            <FinalDropdown
              name="type"
              label={Translate.string('Type')}
              placeholder={Translate.string('No type selected')}
              options={sessionTypes}
              selection
            />
          )}
          <FinalLocationField
            name="location_data"
            label={Translate.string('Default location')}
            description={Translate.string('Default location for blocks inside the session.')}
            parent={{title: 'TODO Conference name here', type: Translate.string('Event')}}
          />
          <FinalSessionColorPicker name="colors" label={Translate.string('Colors')} />
        </FinalModalForm>
      )}
    </>
  );
}
