import contributionCreateURL from 'indico-url:contributions.api_create_contrib';
import sessionBlockCreateURL from 'indico-url:sessions.api_create_session_block';
import breakCreateURL from 'indico-url:timetable.api_create_break';

import _ from 'lodash';
import moment from 'moment';
import React, {useState} from 'react';
import {useDispatch} from 'react-redux';
import {Button, Divider, Header, Segment} from 'semantic-ui-react';

import {SessionSelect} from 'indico/react/components/SessionSelect';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import {ContributionFormFields} from '../../../contributions/client/js/ContributionForm';
import {SessionBlockFormFields} from '../../../sessions/client/js/SessionBlockForm';

import * as actions from './actions';
import {BreakFormFields} from './BreakForm';
import {EntryType, TopLevelEntry} from './types';

// Generic models

interface EntryColors {
  background: string;
  text: string;
}

interface DraftEntry {
  title: string;
  duration: number;
  person_links: any[];
  keywords: string[];
  references: string[];
  location_data: object;
  start_dt: Date;
  conveners?: any[];
  colors?: EntryColors;
}

// Prop interface
interface TimetableCreateModalProps {
  eventId: number;
  newEntry: any;
  onClose?: () => void;
  onSubmit?: () => void;
}

const TimetableCreateModal: React.FC<TimetableCreateModalProps> = ({
  eventId,
  newEntry,
  onClose = () => null,
  onSubmit = () => null,
}) => {
  const dispatch = useDispatch();

  const personLinkFieldParams = {
    allowAuthors: true,
    canEnterManually: true,
    defaultSearchExternal: false,
    extraParams: {},
    hasPredefinedAffiliations: true,
    nameFormat: 'first_last',
  };

  const initialValues: DraftEntry = {
    title: '',
    duration: newEntry.duration * 60,
    person_links: [],
    keywords: [],
    references: [],
    location_data: {inheriting: false},
    start_dt: newEntry.startDt.format('YYYY-MM-DDTHH:mm:ss'),
    conveners: [],
  };

  const forms: {[key in EntryType]: React.ReactElement} = {
    [EntryType.Contribution]: (
      <ContributionFormFields
        eventId={eventId}
        initialValues={initialValues}
        personLinkFieldParams={personLinkFieldParams}
      />
    ),
    [EntryType.SessionBlock]: (
      <>
        <SessionSelect eventId={eventId} required />
        <SessionBlockFormFields eventId={eventId} locationParent={undefined} />
      </>
    ),
    [EntryType.Break]: (
      <BreakFormFields eventId={eventId} locationParent={undefined} initialValues={initialValues} />
    ),
  };

  const [activeForm, setActiveForm] = useState(Object.keys(forms)[0]);

  const mapDataToEntry = (data: any): TopLevelEntry => {
    const {
      id,
      title,
      type: objType,
      duration,
      start_dt: startDt,
      colors,
      y,
      x,
      column,
      maxColumn,
    } = data;
    let type: EntryType = EntryType.SessionBlock;

    switch (objType) {
      case 'BREAK':
        type = EntryType.Break;
        break;
      case 'CONTRIBUTION':
        type = EntryType.Contribution;
        break;
      case 'SESSION_BLOCK':
        type = EntryType.SessionBlock;
        break;
    }

    return {
      id: id || -1,
      type,
      title,
      duration,
      startDt: moment(startDt),
      textColor: colors ? colors.text : '',
      backgroundColor: colors ? colors.background : '',
      x: x || 0,
      y: y || 0,
      column: column || 0,
      maxColumn: maxColumn || 0,
    };
  };

  const handleSubmitContribution = async data => {
    return await indicoAxios.post(contributionCreateURL({event_id: eventId}), data);
  };

  const handleSubmitSessionBlock = async data => {
    // data = _.omitBy(data, 'conveners'); // TODO person links
    // data.conveners = [];
    data.start_dt = new Date(data.start_dt).toISOString();
    return await indicoAxios.post(
      sessionBlockCreateURL({event_id: eventId, session_id: data.session_id}),
      data
    );
  };

  // TODO: Implement logic for breaks
  const handleSubmitBreak = async data => {
    data.start_dt = new Date(data.start_dt).toISOString();
    return await indicoAxios.post(breakCreateURL({event_id: eventId}), data);
  };

  const handleSubmit = async data => {
    const submitHandlers = {
      [EntryType.Contribution]: handleSubmitContribution,
      [EntryType.SessionBlock]: handleSubmitSessionBlock,
      [EntryType.Break]: handleSubmitBreak,
    };

    const submitHandler = submitHandlers[activeForm];

    if (!submitHandler) {
      throw new Error('Invalid form or no submit function found');
    }

    // TODO: (Ajob) Make sure that all create fns return the same way
    const {
      data: {type, object: resData},
    } = await submitHandler(data);

    resData.duration /= 60;

    const newTopLevelEntry = mapDataToEntry({type, ...resData});
    dispatch(actions.createEntry(newTopLevelEntry.type, newTopLevelEntry));
    onSubmit();
    onClose();
  };

  const changeForm = (key: string) => {
    setActiveForm(key);
  };

  const btnNames = {
    [EntryType.Contribution]: Translate.string('Contribution'),
    [EntryType.SessionBlock]: Translate.string('Session Block'),
    [EntryType.Break]: Translate.string('Break'),
  };
  return (
    <FinalModalForm
      id="contribution-form"
      onClose={onClose}
      onSubmit={handleSubmit}
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
        <div>
          {Object.keys(forms).map(key => (
            <Button
              key={key}
              type="button"
              onClick={() => {
                changeForm(key);
              }}
              color={activeForm === key ? 'blue' : undefined}
            >
              {btnNames[key]}
            </Button>
          ))}
        </div>
      </Segment>
      <Divider />
      {forms[activeForm]}
    </FinalModalForm>
  );
};

export default TimetableCreateModal;
