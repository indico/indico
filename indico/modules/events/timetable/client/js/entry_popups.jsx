// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {createPortal} from 'react-dom';
import {useSelector} from 'react-redux';
import {
  Button,
  ButtonGroup,
  Card,
  Dropdown,
  DropdownItem,
  DropdownMenu,
  Icon,
} from 'semantic-ui-react';

import './Entry.module.scss';
import * as selectors from './selectors';
import {getEntryColor} from './utils';

function ColoredDot({color}) {
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

ColoredDot.propTypes = {
  color: PropTypes.string.isRequired,
};

function CardItem({icon, children}) {
  return (
    <Card.Description style={{marginTop: 10, display: 'flex', alignItems: 'center', gap: 5}}>
      <Icon name={icon} size="large" />
      {children}
    </Card.Description>
  );
}

CardItem.propTypes = {
  icon: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
};

function Break({entry, onClose}) {
  const startTime = moment(entry.startDt).format('HH:mm');
  const endTime = moment(entry.startDt)
    .add(entry.duration, 'minutes')
    .format('HH:mm');

  return (
    <Card fluid>
      <Card.Content style={{paddingLeft: 30, paddingBottom: 30}}>
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
        <CardItem icon="clock outline">
          {startTime}-{endTime}
        </CardItem>
        <CardItem icon="map marker alternate">Room 101</CardItem>
      </Card.Content>
    </Card>
  );
}

Break.propTypes = {
  entry: PropTypes.object.isRequired,
  onClose: PropTypes.func.isRequired,
};

function Contribution({entry, onClose}) {
  const sessions = useSelector(selectors.getSessions);
  const {backgroundColor} = getEntryColor(entry, sessions);
  const startTime = moment(entry.startDt).format('HH:mm');
  const endTime = moment(entry.startDt)
    .add(entry.duration, 'minutes')
    .format('HH:mm');

  return (
    <Card fluid>
      <Card.Content style={{paddingLeft: 30, paddingBottom: 30}}>
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
        <CardItem icon="clock outline">
          {startTime}-{endTime}
        </CardItem>
        <CardItem icon="map marker alternate">Room 101</CardItem>
        <CardItem icon="microphone">John Doe</CardItem>
        <CardItem icon="file powerpoint outline">slides.pptx</CardItem>
      </Card.Content>
    </Card>
  );
}

Contribution.propTypes = {
  entry: PropTypes.object.isRequired,
  onClose: PropTypes.func.isRequired,
};

function Block({entry, onClose}) {
  const sessions = useSelector(selectors.getSessions);
  const {backgroundColor} = getEntryColor(entry, sessions);
  const startTime = moment(entry.startDt).format('HH:mm');
  const endTime = moment(entry.startDt)
    .add(entry.duration, 'minutes')
    .format('HH:mm');
  const title = entry.slotTitle ? `${entry.title}: ${entry.slotTitle}` : entry.title;

  return (
    <Card fluid>
      <Card.Content style={{paddingLeft: 30, paddingBottom: 30}}>
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
        <CardItem icon="clock outline">
          {startTime}-{endTime}
        </CardItem>
        <CardItem icon="map marker alternate">Room 101</CardItem>
        <CardItem icon="microphone">John Doe</CardItem>
        <CardItem icon="file powerpoint outline">slides.pptx</CardItem>
      </Card.Content>
    </Card>
  );
}

Block.propTypes = {
  entry: PropTypes.object.isRequired,
  onClose: PropTypes.func.isRequired,
};

export function TimetablePopup({onClose, type, entry, rect}) {
  return createPortal(
    <div
      style={{
        position: 'absolute',
        top: window.scrollY + rect.y - rect.height / 2 + 30,
        left: window.scrollX + rect.x + rect.width / 2 - 250,
        zIndex: 1000,
        minWidth: 500,
        maxWidth: 500,
      }}
    >
      {type === 'break' && <Break entry={entry} onClose={onClose} />}
      {type === 'contrib' && <Contribution entry={entry} onClose={onClose} />}
      {type === 'block' && <Block entry={entry} onClose={onClose} />}
    </div>,
    document.body
  );
}

TimetablePopup.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  type: PropTypes.string.isRequired,
  entry: PropTypes.object.isRequired,
  rect: PropTypes.object.isRequired,
};
