// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import breakURL from 'indico-url:timetable.tt_break_rest';
import contributionURL from 'indico-url:timetable.tt_contrib_rest';
import sessionBlockURL from 'indico-url:timetable.tt_session_block_rest';

import moment from 'moment';
import React from 'react';
import {useSelector, useDispatch} from 'react-redux';
import {
  Button,
  ButtonGroup,
  Card,
  Dropdown,
  DropdownItem,
  DropdownMenu,
  Icon,
  Popup,
  SemanticICONS,
} from 'semantic-ui-react';

import './Entry.module.scss';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import * as actions from './actions';
import {formatTimeRange} from './i18n';
import * as selectors from './selectors';
import {BreakEntry, ContribEntry, BlockEntry, EntryType} from './types';
import {getEntryColor, mapTTDataToEntry} from './utils';

function ColoredDot({color}: {color: string}) {
  return (
    <div
      style={{
        width: 15,
        minWidth: 15,
        height: 15,
        borderRadius: '50%',
        backgroundColor: color,
      }}
    />
  );
}

function CardItem({icon, children}: {icon: SemanticICONS; children: React.ReactNode}) {
  return (
    <Card.Description style={{marginTop: 10, display: 'flex', alignItems: 'center', gap: 5}}>
      <Icon name={icon} size="large" />
      {children}
    </Card.Description>
  );
}

function TimetablePopupContent({
  entry,
  onClose,
}: {
  entry: BlockEntry | ContribEntry | BreakEntry;
  onClose: () => void;
}) {
  const dispatch = useDispatch();

  const {type} = entry;
  const title = 'sessionTitle' in entry ? entry.sessionTitle : entry.title;
  const sessions = useSelector(selectors.getSessions);
  const {backgroundColor} = getEntryColor(entry, sessions);
  const startTime = moment(entry.startDt);
  const endTime = moment(entry.startDt).add(entry.duration, 'minutes');
  let draftEntry = {...entry, duration: entry.duration};
  const eventId = useSelector(selectors.getEventId);

  const onEdit = async (e: MouseEvent) => {
    onClose();
    e.stopPropagation();
    console.group(draftEntry);
    console.log('drat entry entry');
    console.log(draftEntry);
    if (draftEntry.id) {
      // TODO: (Ajob) Requires cleanup of old draftEntry strategy for editing as we now take data from the get request
      const editURL = {
        [EntryType.Contribution]: contributionURL,
        [EntryType.SessionBlock]: sessionBlockURL,
        [EntryType.Break]: breakURL,
      }[type];
      const editId = {
        [EntryType.Contribution]: entry.contributionId,
        [EntryType.SessionBlock]: entry.sessionBlockId,
        [EntryType.Break]: entry.breakId,
      }[type];

      const {data} = await indicoAxios.get(editURL({event_id: eventId, [`${type}_id`]: editId}));
      data['type'] = type;
      draftEntry = mapTTDataToEntry(data);
      dispatch(actions.setDraftEntry(draftEntry));
    }
  };

  return (
    <Card fluid style={{minWidth: 400, boxShadow: 'none'}}>
      <Card.Content>
        <Card.Header>
          <div style={{display: 'flex', justifyContent: 'flex-end', gap: 5}}>
            <ButtonGroup>
              <Button icon="edit" onClick={onEdit} />
              {/* TODO: (Ajob) Evaluate if we actually need the button below */}
              {/* <Button icon="paint brush" /> */}
              <Button icon="trash" />
              {type === EntryType.SessionBlock && (
                <Dropdown button inline icon="ellipsis vertical">
                  <DropdownMenu>
                    <DropdownItem>
                      {/* Implement session edit or redirect to page */}
                      <Icon name="edit" />
                      <Translate>Edit session</Translate>
                    </DropdownItem>
                    <DropdownItem>
                      <Icon name="shield" />
                      <Translate>Edit session protection</Translate>
                    </DropdownItem>
                  </DropdownMenu>
                </Dropdown>
              )}
            </ButtonGroup>
            <ButtonGroup>
              <Button
                icon="close"
                onClick={e => {
                  e.stopPropagation();
                  onClose();
                }}
              />
            </ButtonGroup>
          </div>
        </Card.Header>
        <Card.Header style={{marginTop: 20, marginLeft: 4, marginBottom: 20, fontSize: '1.6em'}}>
          <div style={{display: 'flex', gap: 10, alignItems: 'center'}}>
            <ColoredDot color={backgroundColor} />
            <div>{title}</div>
          </div>
        </Card.Header>
        {/* TODO: (Ajob) Replace dummy data below */}
        <CardItem icon="clock outline">{formatTimeRange('en', startTime, endTime)}</CardItem>
        <CardItem icon="map marker alternate">Room 101</CardItem>
        {type !== EntryType.Break && (
          <>
            <CardItem icon="microphone">John Doe</CardItem>
            <CardItem icon="file powerpoint outline">slides.pptx</CardItem>
          </>
        )}
      </Card.Content>
    </Card>
  );
}

export function TimetablePopup({
  trigger,
  onClose,
  entry,
}: {
  trigger: React.ReactNode;
  onClose: () => void;
  entry: BreakEntry | ContribEntry | BlockEntry;
}) {
  return (
    <Popup
      trigger={trigger}
      on="click"
      position="top center"
      open
      onClose={onClose}
      basic
      hideOnScroll
    >
      <TimetablePopupContent entry={entry} onClose={onClose} />
    </Popup>
  );
}
