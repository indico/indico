// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import breakCreateURL from 'indico-url:timetable.tt_break_create';
import breakURL from 'indico-url:timetable.tt_break_rest';
import contributionCreateURL from 'indico-url:timetable.tt_contrib_create';
import contributionURL from 'indico-url:timetable.tt_contrib_rest';
import sessionBlockCreateURL from 'indico-url:timetable.tt_session_block_create';
import sessionBlockURL from 'indico-url:timetable.tt_session_block_rest';

import _ from 'lodash';
import React, {useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Button, Divider, Header, Message, Segment} from 'semantic-ui-react';

import {FinalSubmitButton} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {snakifyKeys} from 'indico/utils/case';

import {ContributionFormFields} from '../../../contributions/client/js/ContributionForm';
import {SessionBlockFormFields} from '../../../sessions/client/js/SessionBlockForm';

import * as actions from './actions';
import {BreakFormFields} from './BreakForm';
import * as selectors from './selectors';
import {SessionSelect} from './SessionSelect';
import {EntryType, Session} from './types';
import {mapTTDataToEntry} from './utils';

// Generic models

interface EntryColors {
  background: string;
  text: string;
}

interface LocationData {
  inheriting: boolean;
  address?: string;
  room_id?: string;
  room_name?: string;
  venue_id?: string;
  venue_name?: string;
}

interface PersonLink {
  email: string;
  first_name: string;
  last_name: string;
  roles: string[];
  title: string;
  type: string;
  phone?: string;
  address?: string;
  affiliation?: string;
  affiliation_id?: number;
}

// TODO: (Ajob) Make an interface for each entry and then make
//              the draftentry the union of it.
interface DraftEntry {
  title: string;
  duration: number;
  keywords: string[];
  references: string[];
  location_data: LocationData;
  start_dt: Date;
  person_links?: PersonLink[];
  description?: string;
  colors?: EntryColors;
  session_id?: number;
  code?: string;
  board_number?: string;
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
  // Within this timetable we only care about the database ID,
  // not the unique ID generated for the timetable
  const {objId} = entry;
  const isEditing = !!objId;
  const personLinkFieldParams = {
    allowAuthors: true,
    canEnterManually: true,
    defaultSearchExternal: false,
    extraParams: {},
    hasPredefinedAffiliations: true,
    nameFormat: 'first_last',
  };

  const initialValues: DraftEntry = {
    title: entry.title,
    description: entry.description,
    person_links: entry.personLinks || [],
    keywords: entry.keywords || [],
    references: entry.references || [],
    // TODO: (Ajob) Clean up the location data
    location_data: snakifyKeys(entry.location) || {inheriting: false},
    // TODO: (Ajob) Check how we can clean up the required format
    //       as it seems like Contributions need it to be without tzinfo
    start_dt: entry.startDt.format(),
    duration: entry.duration * 60, // Minutes to seconds
    session_id: entry.sessionId,
    board_number: entry.boardNumber,
    code: entry.code,
    colors: entry.colors,
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
        <SessionBlockFormFields
          eventId={eventId}
          extraOptions={extraOptions}
          locationParent={null}
        />
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
        hasParent={entry.parentId !== undefined}
      />
    ),
  };

  // TODO: (Ajob) Implement properly in next issue on editing existing entries
  const [activeType, setActiveType] = useState(isEditing ? entry.type : Object.keys(forms)[0]);

  const _handleCreateContribution = async data => {
    data = _.pick(data, [
      'title',
      'description',
      'duration',
      'person_links',
      'keywords',
      'references',
      'location_data',
      'inheriting',
      'start_dt',
      'keywords',
      'board_number',
      'code',
    ]);
    return await indicoAxios.post(contributionCreateURL({event_id: eventId}), data);
  };

  const _handleCreateSessionBlock = async data => {
    data.conveners = data.person_links;
    data = _.pick(data, [
      'session_id',
      'title',
      'description',
      'duration',
      'location_data',
      'inheriting',
      'start_dt',
      'conveners',
      'code',
    ]);
    const resData = await indicoAxios.post(sessionBlockCreateURL({event_id: eventId}), data);
    resData['person_links'] = resData['conveners'];
    delete resData['conveners'];
    return resData;
  };

  // TODO: Implement logic for breaks
  const _handleCreateBreak = async data => {
    data = _.pick(data, [
      'title',
      'description',
      'break',
      'duration',
      'location_data',
      'inheriting',
      'start_dt',
      'colors',
    ]);
    return await indicoAxios.post(breakCreateURL({event_id: eventId}), data);
  };

  const _handleEditContribution = async data => {
    return indicoAxios.patch(contributionURL({event_id: eventId, contrib_id: objId}), data);
  };

  const _handleEditSessionBlock = async data => {
    return indicoAxios.patch(sessionBlockURL({event_id: eventId, session_block_id: objId}), data);
  };

  const _handleEditBreak = async data => {
    return indicoAxios.patch(breakURL({event_id: eventId, break_id: objId}), data);
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

    const submitHandler = submitHandlers[activeType];

    if (!submitHandler) {
      throw new Error('Invalid form or no submit function found');
    }

    if (data['start_dt']) {
      data['start_dt'] =
        activeType === EntryType.Contribution
          ? entry.startDt.format('YYYY-MM-DDTHH:mm:ss')
          : entry.startDt.format();
    }

    const submitData = snakifyKeys(data);
    // TODO: (Ajob) Remove once personlinks is fixed
    if (isEditing) {
      delete submitData['person_links'];
    }

    const {data: resData} = await submitHandler(submitData);
    resData['type'] = activeType;

    const resEntry = mapTTDataToEntry(resData);

    if (isEditing) {
      dispatch(actions.updateEntry(activeType, resEntry));
    } else {
      dispatch(actions.createEntry(activeType, resEntry));
    }

    onSubmit();
    onClose();
  };

  const changeForm = (key: EntryType) => {
    setActiveType(key);
    if (key === EntryType.SessionBlock && !sessionValues.length) {
      forms[activeType];
    }
  };

  const meetsSubmitConditions = () => {
    // Allows to prevent submitting with pre-conditions, such as
    // not having any sessions available for session blocks. Can
    // be extended for other conditions and forms.
    if (activeType === EntryType.SessionBlock) {
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
                  color={activeType === key ? 'blue' : undefined}
                >
                  {typeLongNames[key]}
                </Button>
              ))}
            </div>
          </Segment>
          <Divider />
        </>
      )}
      {forms[activeType]}
    </FinalModalForm>
  );
};

export default TimetableManageModal;
