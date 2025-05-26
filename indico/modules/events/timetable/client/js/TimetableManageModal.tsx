// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import breakCreateURL from 'indico-url:timetable.api_create_break';
import contributionCreateURL from 'indico-url:timetable.api_create_contrib';
import sessionBlockCreateURL from 'indico-url:timetable.api_create_session_block';

import _ from 'lodash';
import moment from 'moment';
import React, {useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Button, Divider, Header, Message, Segment} from 'semantic-ui-react';

import {FinalSubmitButton} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import {ContributionFormFields} from '../../../contributions/client/js/ContributionForm';
import {SessionBlockFormFields} from '../../../sessions/client/js/SessionBlockForm';

import * as actions from './actions';
import {BreakFormFields} from './BreakForm';
import * as selectors from './selectors';
import {SessionSelect} from './SessionSelect';
import {EntryType, Session, TopLevelEntry} from './types';
import {mapPersonLinkToSchema} from './utils';

// Generic models

interface EntryColors {
  background: string;
  text: string;
}

// TOOD: (Ajob) Make an interface for each entry and then make
//              the draftentry the union of it.
interface DraftEntry {
  title: string;
  duration: number;
  keywords: string[];
  references: string[];
  location_data: object;
  start_dt: Date;
  person_links?: any[];
  description?: string;
  colors?: EntryColors;
  session_id?: number;
  code?: string;
  id?: number;
}

// Prop interface
interface TimetableManageModalProps {
  eventId: number;
  // TODO: (Ajob) Replace with proper passed entry, probably define it higher in hierarchy
  entry: any;
  onClose?: () => void;
  onSubmit?: () => void;
}

const TimetableManageModal: React.FC<TimetableManageModalProps> = ({
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
    title: entry.title || '',
    description: entry.description || '',
    person_links: entry.person_links || [],
    keywords: entry.keywords || [],
    references: entry.references || [],
    location_data: {inheriting: false},
    start_dt: entry.startDt.format('YYYY-MM-DDTHH:mm:ss'),
    duration: entry.duration * 60, // Minutes to seconds
    session_id: entry.session_id || null,
    code: entry.code || null,
  };

  const typeLongNames = {
    [EntryType.Contribution]: Translate.string('Contribution'),
    [EntryType.SessionBlock]: Translate.string('Session Block'),
    [EntryType.Break]: Translate.string('Break'),
  };

  const sessions = useSelector(selectors.getSessions);

  const sessionValues: Session[] = Object.values(sessions);

  const extraOptions = {
    minStartDt: useSelector(selectors.getEventStartDt),
    maxEndDt: useSelector(selectors.getEventEndDt),
  };

  const forms: {[key in EntryType]: React.ReactElement} = {
    [EntryType.Contribution]: (
      <ContributionFormFields
        eventId={eventId}
        initialValues={initialValues}
        personLinkFieldParams={personLinkFieldParams}
        extraOptions={extraOptions}
      />
    ),
    [EntryType.SessionBlock]: sessionValues.length ? (
      <>
        {!isEditing && <SessionSelect sessions={sessionValues} required />}
        <SessionBlockFormFields eventId={eventId} extraOptions={extraOptions} />
      </>
    ) : (
      <Message
        icon="question circle"
        header={Translate.string('No sessions available')}
        color="yellow"
        content={Translate.string('Please create a session before creating a session block.')}
      />
    ),
    [EntryType.Break]: (
      <BreakFormFields
        eventId={eventId}
        locationParent={undefined}
        initialValues={initialValues}
        extraOptions={extraOptions}
      />
    ),
  };

  // TODO: (Ajob) Implement properly in next issue on editing existing entries
  const [activeForm, setActiveForm] = useState(isEditing ? entry.type : Object.keys(forms)[0]);

  const _mapDataToEntry = (data): TopLevelEntry => {
    const {
      type: rawType,
      start_dt: startDt,
      id,
      duration,
      object: {title, colors, session_id: sessionId, persons},
    } = data;

    const type = {
      BREAK: EntryType.Break,
      CONTRIBUTION: EntryType.Contribution,
      SESSION_BLOCK: EntryType.SessionBlock,
    }[rawType];

    if (!type) {
      throw new Error('Invalid entry type', rawType);
    }

    const mappedObj = {
      id: id || -1,
      type,
      title,
      duration: duration / 60,
      startDt: moment(startDt),
      x: 0,
      y: 0,
      column: 0,
      maxColumn: 0,
      children: [],
      textColor: colors ? colors.text : '',
      backgroundColor: colors ? colors.background : '',
      sessionId: sessionId || null,
    };
    return mappedObj;
  };

  const _handleCreateContribution = async data => {
    data.person_links = data.person_links.map(mapPersonLinkToSchema);
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

  const _handleCreateSessionBlock = async data => {
    data.conveners = data.person_links.map(mapPersonLinkToSchema);
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
  const _handleCreateBreak = async data => {
    data = _.pick(data, ['title', 'duration', 'location_data', 'inheriting', 'start_dt', 'colors']);
    return await indicoAxios.post(breakCreateURL({event_id: eventId}), data);
  };

  const _handleEditContribution = async data => {
    // TODO: (Ajob) Implement edit contribution
    return data;
  };

  const _handleEditSessionBlock = async data => {
    // TODO: (Ajob) Implement edit session block
    return data;
  };

  const _handleEditBreak = async data => {
    // TODO: (Ajob) Implement edit break
    return data;
  };

  const handleSubmit = async data => {
    const submitHandlers = isEditing
      ? {
          [EntryType.Contribution]: _handleEditContribution,
          [EntryType.SessionBlock]: _handleEditSessionBlock,
          [EntryType.Break]: _handleEditBreak,
        }
      : {
          [EntryType.Contribution]: _handleCreateContribution,
          [EntryType.SessionBlock]: _handleCreateSessionBlock,
          [EntryType.Break]: _handleCreateBreak,
        };

    const submitHandler = submitHandlers[activeForm];

    if (!submitHandler) {
      throw new Error('Invalid form or no submit function found');
    }

    const {data: resData} = await submitHandler(data);
    const newTopLevelEntry = _mapDataToEntry(resData);

    if (isEditing) {
      // TODO: (Ajob) Implement editing existing entries
      // dispatch(actions.updateEntry(newTopLevelEntry));
    } else {
      dispatch(actions.createEntry(newTopLevelEntry.type, newTopLevelEntry));
    }
    onSubmit();
    onClose();
  };

  const changeForm = (key: EntryType) => {
    setActiveForm(key);
    if (key === EntryType.SessionBlock && !sessionValues.length) {
      forms[activeForm];
    }
  };

  const meetsSubmitConditions = () => {
    // Allows to prevent submitting with pre-conditions, such as
    // not having any sessions available for session blocks. Can
    // be extended for other conditions and forms.
    if (activeForm === EntryType.SessionBlock) {
      return !!sessionValues.length;
    }
    return true;
  };

  return (
    <FinalModalForm
      id="tt-create"
      onClose={onClose}
      onSubmit={handleSubmit}
      initialValues={initialValues}
      disabledUntilChange={false}
      keepDirtyOnReinitialize
      size="small"
      header={
        isEditing
          ? `${Translate.string('Edit')} ${typeLongNames[entry.type]}`
          : Translate.string('Create new timetable entry')
      }
      noSubmitButton
      extraActions={
        meetsSubmitConditions() ? (
          <FinalSubmitButton
            form="final-modal-form-tt-create"
            label={Translate.string('Submit')}
            disabledUntilChange
          />
        ) : null
      }
    >
      {!isEditing && (
        <>
          <Segment textAlign="center">
            <Header as="h4">
              <Translate>Entry Type</Translate>
            </Header>
            <div>
              {Object.keys(forms).map((key: EntryType) => (
                <Button
                  key={key}
                  type="button"
                  onClick={() => {
                    changeForm(key);
                  }}
                  color={activeForm === key ? 'blue' : undefined}
                >
                  {typeLongNames[key]}
                </Button>
              ))}
            </div>
          </Segment>
          <Divider />
        </>
      )}
      {forms[activeForm]}
    </FinalModalForm>
  );
};

export default TimetableManageModal;
