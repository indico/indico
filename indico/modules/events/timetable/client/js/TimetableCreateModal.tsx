import React, {useState} from 'react';
import {Modal, Button, Divider} from 'semantic-ui-react';

import { FinalDatePicker } from 'indico/react/components';
import {FinalInput, FinalTextArea} from 'indico/react/forms';
import { FinalDuration, FinalField } from 'indico/react/forms/fields';
import { FinalModalForm } from 'indico/react/forms/final-form';
import { Translate } from 'indico/react/i18n';

import {ContributionCreateForm, ContributionFormFields} from '../../../contributions/client/js/ContributionForm';
// import {SessionBlockCreateForm} from 'indico/modules/events/sessions/client/js/SessionBlockForm';

interface TimetableCreateModalProps {
  open: boolean;
  onClose: () => void;
  newEntry: any;
}

const TimetableCreateModal: React.FC<TimetableCreateModalProps> = ({open, onClose, newEntry}) => {
  console.log('A new entry!', newEntry)
  const forms = {
    'Contribution': (
      <ContributionFormFields
        eventId={5}
        initialValues={{duration: newEntry?.duration * 60, start_dt: newEntry?.startDt}}
      />
    ),
    'Session Block': (<FinalInput label="Dummy field for session block" name="sessionBlock" />),
  }
  const [activeForm, setActiveForm] = useState(Object.keys(forms)[0]);

  const renderForm = () => forms[activeForm];

  return (
    <FinalModalForm
        id="contribution-form"
        onSubmit={() => ({})}
        onClose={onClose}
        initialValues={{}}
        size="small"
        header={Translate.string('Create new timetable entry')}
    >
      <Button.Group>
        {Object.keys(forms).map((key) => (
          <Button key={key} onClick={() => setActiveForm(key)} active={activeForm === key}>{key}</Button>
        ))}
      </Button.Group>
      <Divider />
      {/* <FinalDuration name="duration" label={undefined} defaultValue={undefined} /> */}
      {activeForm && renderForm()}
    </FinalModalForm>
  );
};

export default TimetableCreateModal;