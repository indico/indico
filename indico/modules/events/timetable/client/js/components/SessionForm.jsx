import React, {useState} from 'react';
import {Button} from 'semantic-ui-react';

import {FinalLocationField, FinalSessionColorPicker} from 'indico/react/components';
import {FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalDropdown, FinalTimePicker} from 'indico/react/forms/fields';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';

export default function SessionForm() {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setModalOpen(true)}>Open Session Form</Button>
      {modalOpen && (
        <FinalModalForm
          id="session-form"
          header={Translate.string('Edit session ???')}
          onSubmit={() => {}}
          onClose={() => setModalOpen(false)}
        >
          <FinalInput name="title" label="Session title" autoFocus required />
          <FinalInput
            name="code"
            label={Translate.string('Session code')}
            description={Translate.string(
              'The code that will identify the session in the Book of Abstracts.'
            )}
          />
          <FinalTextArea name="description" label={Translate.string('Description')} />
          <FinalTimePicker
            name="default_contribution_duration"
            label={Translate.string('Default contribution duration')}
            description={Translate.string(
              'Duration that a contribution created within this session will have by default.'
            )}
            required
          />
          <FinalDropdown
            name="type"
            label={Translate.string('Type')}
            placeholder={Translate.string('No type selected')}
            options={[{text: Translate.string('Poster'), value: 'poster'}]}
            selection
          />
          <FinalLocationField
            name="location"
            label={Translate.string('Default location')}
            description={Translate.string('Default location for blocks inside the session.')}
            parent={{title: 'TODO Conference name here', type: Translate.string('Event')}}
          />
          <FinalSessionColorPicker name="color" label={Translate.string('Colors')} />
        </FinalModalForm>
      )}
    </>
  );
}
