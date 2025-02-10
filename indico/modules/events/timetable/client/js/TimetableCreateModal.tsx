import contributionCreateURL from 'indico-url:contributions.api_create_contrib';

import React, {useState} from 'react';
import {Button, Divider} from 'semantic-ui-react';
import {FormSpy} from 'react-final-form';

import {FinalModalForm, handleSubmitError} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import {ContributionFormFields} from '../../../contributions/client/js/ContributionForm';
import {SessionFormFields} from '../../../sessions/client/js/SessionForm';
// import {SessionBlockCreateForm} from 'indico/modules/events/sessions/client/js/SessionBlockForm';

interface TimetableCreateModalProps {
  eventId: number;
  newEntry: any;
  onClose: () => void;
}

const TimetableCreateModal: React.FC<TimetableCreateModalProps> = ({
  eventId,
  onClose,
  newEntry,
}) => {
  const personLinkFieldParams = {
    allowAuthors: true,
    canEnterManually: true,
    defaultSearchExternal: false,
    extraParams: {},
    hasPredefinedAffiliations: true,
    nameFormat: 'first_last',
  };

  const initialValues = {
    title: '',
    duration: newEntry.duration * 60,
    person_links: [],
    keywords: [],
    references: [],
    location_data: {inheriting: false},
    custom_fields: {},
    start_dt: newEntry.startDt.format('YYYY-MM-DDTHH:mm:ss'),
  };

  const forms = {
    'Contribution': (
      <ContributionFormFields
        eventId={eventId}
        initialValues={initialValues}
        personLinkFieldParams={personLinkFieldParams}
      />
    ),
    'Session Block': (
      <SessionFormFields eventType="conference" sessionTypes={[]} locationParent={{}} />
    ),
  };

  const [activeForm, setActiveForm] = useState(Object.keys(forms)[1]);
  const [formValues, setFormValues] = useState(initialValues);

  const renderForm = () => forms[activeForm];

  const handleSubmit = async (formData: any) => {
    try {
      await indicoAxios.post(contributionCreateURL({event_id: eventId}), formData);
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
    // never finish submitting to avoid fields being re-enabled
    await new Promise(() => {});
  };

  const changeForm = (key: string) => {
    setActiveForm(key);
  };

  return (
    <FinalModalForm
      id="contribution-form"
      onSubmit={handleSubmit}
      onClose={onClose}
      initialValues={formValues}
      size="small"
      header={Translate.string('Create new timetable entry')}
    >
      <FormSpy
        subscription={{values: true}}
        onChange={({values}) => {
          setFormValues({...formValues, ...values});
        }}
      />
      <Button.Group>
        {Object.keys(forms).map(key => (
          <Button key={key} onClick={() => changeForm(key)} active={activeForm === key}>
            {key}
          </Button>
        ))}
      </Button.Group>
      <Divider />
      {activeForm && renderForm()}
    </FinalModalForm>
  );
};

export default TimetableCreateModal;
