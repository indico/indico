import contributionCreateURL from 'indico-url:contributions.api_create_contrib';

import React, {useState} from 'react';
import {FormSpy} from 'react-final-form';
import {Button, Divider, Header, Segment} from 'semantic-ui-react';

import {SessionSelect} from 'indico/react/components/SessionSelect';
import {FinalModalForm, handleSubmitError} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import {ContributionFormFields} from '../../../contributions/client/js/ContributionForm';
import {SessionBlockFormFields} from '../../../sessions/client/js/SessionBlockForm';
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
    conveners: [],
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
      <>
        {/* <Header as="h3">{Translate.string('Session Block')}</Header> */}
        <SessionSelect eventId={eventId} required />
        <SessionBlockFormFields eventId={eventId} locationParent={undefined} {...initialValues} />
        {/* <Divider />
        <Header as="h3">{Translate.string('Session')}</Header>
        <SessionFormFields eventType="conference" sessionTypes={[]} locationParent={{}} /> */}
      </>
    ),
  };

  const [activeForm, setActiveForm] = useState(Object.keys(forms)[0]);
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
      <Segment textAlign="center">
        <Header as="h4">
          <Translate>Entry Type</Translate>
        </Header>
        {Object.keys(forms).map(key => (
          <Button
            key={key}
            onClick={() => changeForm(key)}
            color={activeForm === key ? 'blue' : undefined}
          >
            {key}
          </Button>
        ))}
      </Segment>
      <Divider />
      {activeForm && renderForm()}
    </FinalModalForm>
  );
};

export default TimetableCreateModal;
