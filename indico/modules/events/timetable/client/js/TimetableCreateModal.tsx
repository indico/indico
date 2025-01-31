import React, {useState} from 'react';
import {Modal, Button, Divider} from 'semantic-ui-react';

import {SessionBlockCreateForm} from 'indico/modules/events/sessions/client/js/SessionBlockForm';
import {FinalInput, FinalTextArea} from 'indico/react/forms';
import { FinalModalForm } from 'indico/react/forms/final-form';
import { Translate } from 'indico/react/i18n';

import {ContributionCreateForm} from '../../../contributions/client/js/ContributionForm';

interface TimetableCreateModalProps {
  open: boolean;
  onClose: () => void;
  newEntry: any;
}

const TimetableCreateModal: React.FC<TimetableCreateModalProps> = ({open, onClose, newEntry}) => {
  const [activeForm, setActiveForm] = useState('contribution');

  const renderForm = () => {
    switch (activeForm) {
      case 'contribution':
        return (
          <ContributionCreateForm
            eventId={5}
            onClose={onClose}
            customFields={[
              {
                id: 1,
                fieldType: 'text',
                title: 'test',
                description: 'Field for testing',
                isRequired: false,
                fieldData: {},
              },
            ]}
            customInitialValues={{duration: newEntry?.duration * 60}}
            includeModal={false}
          />
        );
        case 'session-block':
          return (
            <SessionBlockCreateForm
              eventId={5}
              onClose={onClose}
              customFields={[
                {
                  id: 1,
                  fieldType: 'text',
                  title: 'test',
                  description: 'Field for testing',
                  isRequired: false,
                  fieldData: {},
                },
              ]}
              customInitialValues={{duration: newEntry?.duration * 60}}
              includeModal={false}
            />
          )
      // Add other forms here
      default:
        return null;
    }
  };

  return (
    <FinalModalForm
        id="contribution-form"
        onSubmit={() => ({})}
        onClose={onClose}
        initialValues={{}}
        size="small"
        header={Translate.string('Create new entry')}
    >
      <Button.Group>
        <Button onClick={() => setActiveForm('contribution')}>Contribution</Button>
        <Button onClick={() => setActiveForm('session-block')}>Session Block</Button>
      </Button.Group>
      <Divider />

      <FinalInput name="maintitle" label={Translate.string('Main Title')} autoFocus required type={undefined} nullIfEmpty={undefined} noAutoComplete={undefined} />
      {activeForm && renderForm()}
    </FinalModalForm>
  );
};

export default TimetableCreateModal;