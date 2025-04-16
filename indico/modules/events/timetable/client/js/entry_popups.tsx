// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import entryActionsURL from 'indico-url:timetable.timetable_rest';

import moment from 'moment';
import React from 'react';
import {useDispatch, useSelector} from 'react-redux';
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

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import './Entry.module.scss';
import * as actions from './actions';
import {formatTimeRange} from './i18n';
import * as selectors from './selectors';
import {BreakEntry, ContribEntry, BlockEntry} from './types';
import {formatBlockTitle, getEntryColor} from './utils';

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

function Break({entry, onClose}: {entry: BreakEntry; onClose: () => void}) {
  const dispatch = useDispatch();
  const {id} = entry;
  const startTime = moment(entry.startDt);
  const endTime = moment(entry.startDt).add(entry.duration, 'minutes');
  const eventId = useSelector(selectors.getEventId);

  async function deleteBreak(e) {
    e.stopPropagation();
    const url = entryActionsURL({event_id: eventId, entry_id: id});
    try {
      await indicoAxios.delete(url);
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    dispatch(actions.deleteBreak(entry));
  }

  return (
    <Card fluid style={{minWidth: 400, boxShadow: 'none'}}>
      <Card.Content>
        <Card.Header>
          <div style={{display: 'flex', justifyContent: 'flex-end', gap: 5}}>
            <ButtonGroup>
              <Button icon="edit" />
              <Button icon="paint brush" />
              <Button icon="trash" onClick={deleteBreak} />
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
            <ColoredDot color={entry.backgroundColor} />
            <div>{entry.title}</div>
          </div>
        </Card.Header>
        <Card.Meta style={{marginLeft: 29}}>{entry.description}</Card.Meta>
        <CardItem icon="clock outline">{formatTimeRange('en', startTime, endTime)}</CardItem>
        <CardItem icon="map marker alternate">Room 101</CardItem>
      </Card.Content>
    </Card>
  );
}

function Contribution({entry, onClose}: {entry: ContribEntry; onClose: () => void}) {
  const sessions = useSelector(selectors.getSessions);
  const {backgroundColor} = getEntryColor(entry, sessions);
  const startTime = moment(entry.startDt);
  const endTime = moment(entry.startDt).add(entry.duration, 'minutes');

  return (
    <Card fluid style={{minWidth: 400, boxShadow: 'none'}}>
      <Card.Content>
        <Card.Header>
          <div style={{display: 'flex', justifyContent: 'flex-end', gap: 5}}>
            <ButtonGroup>
              <Button icon="edit" />
              <Button icon="paint brush" />
              <Button icon="trash" />
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
            <div>{entry.title}</div>
          </div>
        </Card.Header>
        <Card.Meta style={{marginLeft: 29}}>{entry.description}</Card.Meta>
        <CardItem icon="clock outline">{formatTimeRange('en', startTime, endTime)}</CardItem>
        <CardItem icon="map marker alternate">Room 101</CardItem>
        <CardItem icon="microphone">John Doe</CardItem>
        <CardItem icon="file powerpoint outline">slides.pptx</CardItem>
      </Card.Content>
    </Card>
  );
}

function Block({entry, onClose}: {entry: BlockEntry; onClose: () => void}) {
  const dispatch = useDispatch();
  const {id} = entry;
  const sessions = useSelector(selectors.getSessions);
  const {backgroundColor} = getEntryColor(entry, sessions);
  const startTime = moment(entry.startDt);
  const endTime = moment(entry.startDt).add(entry.duration, 'minutes');
  const title = formatBlockTitle(entry.sessionTitle, entry.title);
  const eventId = useSelector(selectors.getEventId);

  async function deleteBlock(e) {
    e.stopPropagation();
    const url = entryActionsURL({event_id: eventId, entry_id: id});
    try {
      await indicoAxios.delete(url);
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    dispatch(actions.deleteBlock(id));
  }

  return (
    <Card fluid style={{minWidth: 400, boxShadow: 'none'}}>
      <Card.Content>
        <Card.Header>
          <div style={{display: 'flex', justifyContent: 'flex-end', gap: 5}}>
            <ButtonGroup>
              <Button icon="edit" />
              <Button icon="paint brush" disabled />
              <Button icon="trash" onClick={deleteBlock} />
              <Dropdown button inline icon="ellipsis vertical" disabled>
                <DropdownMenu>
                  <DropdownItem>
                    <Icon name="edit" /> Edit session
                  </DropdownItem>
                  <DropdownItem>
                    <Icon name="shield" />
                    Edit session protection
                  </DropdownItem>
                </DropdownMenu>
              </Dropdown>{' '}
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
        <CardItem icon="clock outline">{formatTimeRange('en', startTime, endTime)}</CardItem>
        <CardItem icon="map marker alternate">Room 101</CardItem>
        <CardItem icon="microphone">John Doe</CardItem>
        <CardItem icon="file powerpoint outline">slides.pptx</CardItem>
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
  let children;
  if (entry.type === 'block') {
    children = <Block entry={entry} onClose={onClose} />;
  } else if (entry.type === 'contrib') {
    children = <Contribution entry={entry} onClose={onClose} />;
  } else {
    children = <Break entry={entry} onClose={onClose} />;
  }

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
      <div onMouseDown={e => e.stopPropagation()} onClick={e => e.stopPropagation()}>
        {children}
      </div>
    </Popup>
  );
}
