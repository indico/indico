// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React from 'react';
import {useSelector} from 'react-redux';
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
  const startTime = entry.startDt;
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
  const sessions = useSelector(selectors.getSessions);
  const {backgroundColor} = getEntryColor(entry, sessions);
  const startTime = moment(entry.startDt);
  const endTime = moment(entry.startDt).add(entry.duration, 'minutes');
  const title = formatBlockTitle(entry.sessionTitle, entry.title);

  return (
    <Card fluid style={{minWidth: 400, boxShadow: 'none'}}>
      <Card.Content>
        <Card.Header>
          <div style={{display: 'flex', justifyContent: 'flex-end', gap: 5}}>
            <ButtonGroup>
              <Button icon="edit" />
              <Button icon="paint brush" />
              <Button icon="trash" />
              <Dropdown button inline icon="ellipsis vertical">
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
      {children}
    </Popup>
  );
}
