// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import React, {useState, useEffect} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {ThunkDispatch} from 'redux-thunk';
import {Button, Divider, Header, Segment} from 'semantic-ui-react';

import {ContributionFormFields} from 'indico/modules/events/contributions/ContributionForm';
import {SessionBlockFormFields} from 'indico/modules/events/sessions/SessionBlockForm';
import {FinalSubmitButton} from 'indico/react/forms';
import {FinalModalForm, getChangedValues, handleSubmitError} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';
import {handleAxiosError} from 'indico/utils/axios';
import {snakifyKeys} from 'indico/utils/case';

import * as actions from './actions';
import {BreakFormFields} from './BreakForm';
import {mapDataToEntry, mapEntryToData} from './mapperUtils';
import * as selectors from './selectors';
import {FinalSessionSelect} from './SessionSelect';
import {ReduxState, BlockEntry, EntryType, Session} from './types';
import {DATE_KEY_FORMAT, mapSessionToTTData} from './utils';

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
  session_block_id?: number;
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
  const dispatch: ThunkDispatch<ReduxState, unknown, actions.Action> = useDispatch();
  const entries = useSelector(selectors.getCurrentEntries);
  const expandedSessionBlock = useSelector(selectors.getExpandedSessionBlock);
  // Within this timetable we only care about the database ID,
  // not the unique ID generated for the timetable
  const {objId, sessionBlockId = expandedSessionBlock?.objId} = entry;
  const isEditing = !!objId;
  const isCreatingChild = !!sessionBlockId;
  const parent = (expandedSessionBlock ||
    entries.find(e => e.id === sessionBlockId)) as Partial<BlockEntry>;
  const personLinkFieldParams = {
    allowAuthors: true,
    canEnterManually: true,
    defaultSearchExternal: false,
    extraParams: {},
    hasPredefinedAffiliations: true,
    nameFormat: 'first_last',
  };
  const extraOptions = {
    minStartDt: useSelector(selectors.getEventStartDt),
    maxEndDt: useSelector(selectors.getEventEndDt),
  };
  let initialStartDt = entry.startDt.format();

  if (parent) {
    extraOptions.minStartDt = moment(parent.startDt);
    extraOptions.maxEndDt = moment(parent.startDt).add(parent.duration, 'minutes');

    initialStartDt = moment
      .min(
        moment(initialStartDt),
        moment(extraOptions.maxEndDt).subtract(entry.duration, 'minutes')
      )
      .format();
  }

  const initialValues: DraftEntry = {
    title: entry.title,
    description: entry.description,
    person_links: entry.personLinks || [],
    keywords: entry.keywords || [],
    references: entry.references || [],
    // TODO: (Ajob) Clean up the location data
    location_data: snakifyKeys(entry.locationData) || {inheriting: false},
    // TODO: (Ajob) Check how we can clean up the required format
    //       as it seems like Contributions need it to be without tzinfo
    start_dt: initialStartDt,
    duration: entry.duration * 60, // Minutes to seconds
    session_id: entry.sessionId,
    session_block_id: entry.sessionBlockId,
    board_number: entry.boardNumber,
    code: entry.code,
    ...(entry.colors && {
      colors: {
        text: entry.colors.color,
        background: entry.colors.backgroundColor,
      },
    }),
  };

  const typeLongNames = {
    [EntryType.Contribution]: Translate.string('Contribution'),
    [EntryType.SessionBlock]: Translate.string('Session Block'),
    [EntryType.Break]: Translate.string('Break'),
  };

  const currentDay = useSelector(selectors.getCurrentDate).format(DATE_KEY_FORMAT);
  const sessionsObj = useSelector(selectors.getSessions);
  const sessions: Session[] = Object.values(sessionsObj);
  const session = sessions.find(s => s.id === entry.sessionId);

  const forms: {[key in EntryType]: React.ReactElement} = {
    [EntryType.Contribution]: (
      <ContributionFormFields
        eventId={eventId}
        initialValues={initialValues}
        personLinkFieldParams={personLinkFieldParams}
        extraOptions={extraOptions}
        locationParent={snakifyKeys(entry.locationParent)}
        sessionBlock={parent}
      />
    ),
    ...(!isCreatingChild
      ? {
          [EntryType.SessionBlock]: (
            <>
              {!isEditing && <FinalSessionSelect sessions={sessions} required />}
              <SessionBlockFormFields
                eventId={eventId}
                extraOptions={extraOptions}
                locationParent={snakifyKeys(entry.locationParent)}
              />
            </>
          ),
        }
      : null),
    [EntryType.Break]: (
      <BreakFormFields
        eventId={eventId}
        locationParent={snakifyKeys(entry.locationParent)}
        initialValues={initialValues}
        extraOptions={extraOptions}
        hasParent={isCreatingChild}
      />
    ),
  };

  // TODO: (Ajob) Implement properly in next issue on editing existing entries
  const [activeType, setActiveType] = useState<EntryType>(
    isEditing ? entry.type : Object.keys(forms)[0]
  );

  const _createSession = async sessionObject => {
    try {
      // TODO: (Ajob) Replace once the back-end schemas allow us a more consistent mapping
      const data = mapSessionToTTData(sessionObject);
      const {session: resSession} = await dispatch(actions.createSession(_.omit(data, 'id')));
      return resSession;
    } catch (error) {
      handleAxiosError(error, true);
    }
  };

  const handleSubmit = async (data: any, form: any) => {
    const sessionObj = data.session_object;
    delete data.session_object;

    if (parent) {
      data.session_block_id = parent.objId;
    }

    if (sessionObj) {
      const sessionId = session?.id ?? sessionObj?.id;

      if (sessionId === -1) {
        const newSession = await _createSession(sessionObj);
        data.session_id = newSession.id;
      } else {
        data.session_id = sessionId;
      }
    }

    // TODO:  (Ajob) The real solution would be to change the personlinkfield, but this
    //        affects many other parts of the code and so for now we will do it like this.
    if (data.person_links || data.conveners) {
      const persons = data.person_links || data.conveners;
      data.person_links = mapEntryToData({personLinks: persons}, true).person_links;
    }

    if (activeType === EntryType.SessionBlock && data.person_links) {
      data.conveners = data.person_links;
    }

    try {
      if (isEditing) {
        const updatedEntry = {...entry, ...mapDataToEntry(data, true)};
        dispatch(
          actions.updateEntry(activeType, updatedEntry, currentDay, getChangedValues(data, form))
        );
      } else {
        dispatch(actions.createEntry(activeType, data));
      }
    } catch (exc) {
      return handleSubmitError(exc);
    }

    onSubmit();
    onClose();
  };

  const changeForm = (key: EntryType) => {
    setActiveType(key);
  };

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        onClose();
      }
    };
    window.addEventListener('keydown', onKeyDown, true);
    return () => window.removeEventListener('keydown', onKeyDown, true);
  }, [onClose]);

  return (
    <FinalModalForm
      id="tt-create"
      onClose={onClose}
      onSubmit={handleSubmit}
      initialValues={initialValues}
      initialValuesEqual={_.isEqual}
      disabledUntilChange={false}
      keepDirtyOnReinitialize
      size="small"
      header={
        isEditing
          ? `${Translate.string('Edit')} ${typeLongNames[entry.type as EntryType]}`
          : Translate.string('Create new timetable entry')
      }
      noSubmitButton
      extraActions={
        <FinalSubmitButton
          form="final-modal-form-tt-create"
          label={Translate.string('Submit')}
          activeSubmitButton
        />
      }
    >
      {!isEditing && (
        <>
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
                    changeForm(key as EntryType);
                  }}
                  primary={activeType === key}
                >
                  {typeLongNames[key as EntryType]}
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
