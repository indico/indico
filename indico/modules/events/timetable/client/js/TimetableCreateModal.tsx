import breakCreateURL from 'indico-url:timetable.api_create_break';
import contributionCreateURL from 'indico-url:timetable.api_create_contrib';
import sessionBlockCreateURL from 'indico-url:timetable.api_create_session_block';

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
import {EntryType, Requestentryect, TopLevelEntry} from './types';

// Generic models

interface EntryColors {
  background: string;
  text: string;
}

// TOOD: (Ajob) Make for each entry an interface and then make
//              the draftentry be the union of it.
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
  session_id?: number;
  code?: string;
  id?: number; // Indicates whether or not we are editing an entry
}

// Prop interface
interface TimetableCreateModalProps {
  eventId: number;
  entry: any;
  onClose?: () => void;
  onSubmit?: () => void;
}

const TimetableCreateModal: React.FC<TimetableCreateModalProps> = ({
  eventId,
  entry,
  onClose = () => null,
  onSubmit = () => null,
}) => {
  const dispatch = useDispatch();

  const isEditing = !!entry.id;

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
    person_links: [],
    keywords: [],
    references: [],
    location_data: {inheriting: false},
    conveners: [],
    start_dt: entry.startDt.format('YYYY-MM-DDTHH:mm:ss'),
    duration: entry.duration * 60, // Minutes to seconds
    session_id: null,
    code: null,
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

  console.log('etype', entry['type']);

  // TODO: (Ajob) Implement properly in next issue on editing existing entries
  const [activeForm, setActiveForm] = useState(isEditing ? entry['type'] : Object.keys(forms)[0]);

  // TODO: (Ajob) Clean up 'Requestentryect' and use that type instead
  const mapDataToEntry = (data: any): TopLevelEntry => {
    const {object} = data;
    delete data['object'];
    data['duration'] /= 60; // Seconds to minutes
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
      session_id: sessionId,
    } = {...object, ...data};

    let type;
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
      default:
        throw new Error('Invalid entry type', objType);
    }

    return {
      id: id || -1,
      type,
      title,
      duration,
      startDt: moment(startDt),
      x: x || 0,
      y: y || 0,
      column: column || 0,
      maxColumn: maxColumn || 0,
      children: [],
      // TODO: (Ajob) Get rid of hardcoded colors
      textColor: colors ? colors.text : '',
      backgroundColor: colors ? colors.background : '',
      sessionId: sessionId ? sessionId : -1,
    };
  };

  const _handleSubmitContribution = async data => {
    data = _.pick(data, [
      'title',
      'duration',
      'person_links',
      'keywords',
      'references',
      'location_data',
      'inheriting',
      'start_dt',
    ]);
    return await indicoAxios.post(contributionCreateURL({event_id: eventId}), data);
  };

  const _handleSubmitSessionBlock = async data => {
    // data = _.omitBy(data, 'conveners'); // TODO person links
    // data.conveners = [];
    // TODO: (Ajob) Evaluate if we should pass the session_id by url or not.
    //              I presume not as we might get in the situation where we
    //              like to create a session while creating a block.
    data = _.pick(data, [
      'title',
      'duration',
      'location_data',
      'inheriting',
      'start_dt',
      'conveners',
      'session_id',
    ]);
    return await indicoAxios.post(sessionBlockCreateURL({event_id: eventId}), data);
  };

  // TODO: Implement logic for breaks
  const _handleSubmitBreak = async data => {
    data = _.pick(data, ['title', 'duration', 'location_data', 'inheriting', 'start_dt']);
    // data.start_dt = new Date(data.start_dt).toISOString();
    return await indicoAxios.post(breakCreateURL({event_id: eventId}), data);
  };

  const handleSubmit = async data => {
    const submitHandlers = {
      [EntryType.Contribution]: _handleSubmitContribution,
      [EntryType.SessionBlock]: _handleSubmitSessionBlock,
      [EntryType.Break]: _handleSubmitBreak,
    };

    const submitHandler = submitHandlers[activeForm];

    if (!submitHandler) {
      throw new Error('Invalid form or no submit function found');
    }

    const {data: resData} = await submitHandler(data);
    const newTopLevelEntry = mapDataToEntry(resData);

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
