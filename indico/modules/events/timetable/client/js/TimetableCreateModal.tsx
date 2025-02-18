import contributionCreateURL from 'indico-url:contributions.api_create_contrib';
import sessionBlockCreateURL from 'indico-url:sessions.api_create_session_block';

import _ from 'lodash';
import React, {useState} from 'react';
import {Button, Divider, Header, Segment} from 'semantic-ui-react';

import {SessionSelect} from 'indico/react/components/SessionSelect';
import {FinalInput} from 'indico/react/forms';
import {FinalModalForm, handleSubmitError} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import {ContributionFormFields} from '../../../contributions/client/js/ContributionForm';
import {SessionBlockFormFields} from '../../../sessions/client/js/SessionBlockForm';

interface TimetableCreateModalProps {
  eventId: number;
  newEntry: any; // TODO: Make proper interface
  onClose: () => void;
}

enum FormType {
  Contribution = 'Contribution',
  SessionBlock = 'Session Block',
  Break = 'Break',
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
    start_dt: newEntry.startDt.format('YYYY-MM-DDTHH:mm:ss'),
    conveners: [],
  };

  const forms: {[key in FormType]: React.ReactElement} = {
    [FormType.Contribution]: (
      <ContributionFormFields
        eventId={eventId}
        initialValues={initialValues}
        personLinkFieldParams={personLinkFieldParams}
      />
    ),
    [FormType.SessionBlock]: (
      <>
        <SessionSelect eventId={eventId} required />
        <SessionBlockFormFields eventId={eventId} locationParent={undefined} {...initialValues} />
      </>
    ),
    [FormType.Break]: (
      <>
        {/* TODO: Make actual Break form */}
        {/*       Includes: Title, Description, Start time, Duration, Location (incl use default), colours */}
        <FinalInput
          name="title"
          label={Translate.string('Title')}
          required
          type={undefined}
          nullIfEmpty={undefined}
          noAutoComplete={undefined}
        />
      </>
    ),
  };

  const [activeForm, setActiveForm] = useState(Object.keys(forms)[0]);

  const handleSubmitContribution = async (data: any) => {
    return await indicoAxios.post(contributionCreateURL({event_id: eventId}), data);
  };

  const handleSubmitSessionBlock = async (data: any) => {
    data = _.omitBy(data, 'conveners'); // TODO person links
    data.conveners = [];
    data.start_dt = new Date(data.start_dt).toISOString();
    return await indicoAxios.post(
      sessionBlockCreateURL({event_id: eventId, session_id: data.session_id}),
      data
    );
  };

  // TODO: Implement logic for breaks
  const handleSubmitBreak = async (formData: any) => {
    return [];
  };

  const handleSubmit = async (formData: any) => {
    try {
      switch (activeForm) {
        case FormType.Contribution:
          await handleSubmitContribution(formData);
          break;
        case FormType.SessionBlock:
          await handleSubmitSessionBlock(formData);
          break;
        case FormType.Break:
          await handleSubmitBreak(formData);
          break;
        default:
          throw new Error('Invalid form');
      }
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
  };

  const changeForm = (key: string) => {
    setActiveForm(key);
  };

  return (
    <FinalModalForm
      id="contribution-form"
      onSubmit={handleSubmit}
      onClose={onClose}
      initialValues={initialValues}
      disabledUntilChange={false}
      keepDirtyOnReinitialize
      size="small"
      header={Translate.string('Create new timetable entry')}
    >
      <Segment textAlign="center">
        <Header as="h4">
          <Translate>Entry Type</Translate>
        </Header>
        {Object.keys(forms).map(key => (
          <Button
            key={key}
            type="button"
            onClick={() => {
              changeForm(key);
            }}
            color={activeForm === key ? 'blue' : undefined}
          >
            {key}
          </Button>
        ))}
      </Segment>
      <Divider />
      {forms[activeForm]}
    </FinalModalForm>
  );
};

export default TimetableCreateModal;
