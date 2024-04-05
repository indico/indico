import React, {useState} from 'react';
import {Button} from 'semantic-ui-react';

import {FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalTimePicker} from 'indico/react/forms/fields';
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
            label="The code that will identify the session in the Book of Abstracts."
          />
          <FinalTextArea name="description" label="Description" />
          <FinalTimePicker
            name="default_contribution_duration"
            label="Default contribution duration"
            required
          />
        </FinalModalForm>
      )}
    </>
  );
}
