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
  List,
  Popup,
  SemanticICONS,
} from 'semantic-ui-react';

import {Translate, Param, Plural, PluralTranslate, Singular} from 'indico/react/i18n';
import './Entry.module.scss';
import {indicoAxios} from 'indico/utils/axios';

import * as actions from './actions';
import {formatTimeRange} from './i18n';
import {ReduxState} from './reducers';
import * as selectors from './selectors';
import {BreakEntry, ContribEntry, BlockEntry, EntryType, PersonLinkRole} from './types';
import {formatBlockTitle, getEntryColor, mapTTDataToEntry} from './utils';

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
    <Card.Description
      style={{marginTop: 10, display: 'flex', alignItems: 'flex-start', gap: 5, textAlign: 'left'}}
    >
      <Icon name={icon} size="large" />
      {children}
    </Card.Description>
  );
}

function EntryPopupContent({entry, onClose}: {entry; onClose: () => void}) {
  const dispatch = useDispatch();
  const {type, title, sessionTitle} = entry;
  const sessions = useSelector(selectors.getSessions);
  const eventId = useSelector(selectors.getEventId);
  const {backgroundColor} = getEntryColor(entry, sessions);
  const startTime = moment(entry.startDt);
  const endTime = moment(entry.startDt).add(entry.duration, 'minutes');

  const session = useSelector((state: ReduxState) =>
    selectors.getSessionById(state, entry.sessionId)
  );

  const _getFileCount = () => {
    const {attachments = {}} = entry;
    const {files = [], folders = []} = attachments;
    return files.length + folders.length;
  };

  const _getOrderedLocationArray = () => {
    const {locationData = {}} = entry;
    const {address, venueName, room} = locationData;
    return Object.values([address, venueName, room]).filter(Boolean);
  };

  const _getPresentersArray = () => {
    const {personLinks = []} = entry;
    return personLinks
      .filter(p => !p.roles || p.roles.includes(PersonLinkRole.SPEAKER))
      .map(p => p.name);
  };

  const onEdit = async (e: MouseEvent) => {
    const {objId} = entry;
    if (!objId) {
      return;
    }

    e.stopPropagation();
    onClose();

    const editURL = {
      [EntryType.Contribution]: contributionURL({event_id: eventId, contrib_id: objId}),
      [EntryType.SessionBlock]: sessionBlockURL({event_id: eventId, session_block_id: objId}),
      [EntryType.Break]: breakURL({event_id: eventId, break_id: objId}),
    }[type];

    const {data} = await indicoAxios.get(editURL);
    data['type'] = type;
    entry = mapTTDataToEntry(data);
    dispatch(actions.setDraftEntry(entry));
  };

  const onCreateChild = async (e: MouseEvent) => {
    e.stopPropagation();
    onClose();
    // WARNING: The entry here would be the sessionBlock
    console.log(session, entry);
    // DONE: (Michel) Get default start time from the session block or the earliest possible start time within the session block
    const newChildStartDt = moment(entry.startDt);
    if (entry.children.length > 0) {
      const childWithLatestEndTime = entry.children.reduce((latest, child) => {
        const childEndTime = moment(child.startDt).add(child.duration, 'minutes');
        const latestEndTime = moment(latest.startDt).add(latest.duration, 'minutes');
        return childEndTime.isAfter(latestEndTime) ? child : latest;
      });
      newChildStartDt = moment(childWithLatestEndTime.startDt).add(
        childWithLatestEndTime.duration,
        'minutes'
      );
    }
    // DONE: (Michel) Get default duration from the session
    const newChildDuration = session.defaultContributionDuration;
    // TODO: (Michel) Get default location from the session block
    // DONE: (Michel) Set draft entry to dummy contribution/ break with the default values gathered
    dispatch(
      actions.setDraftEntry({
        startDt: newChildStartDt,
        duration: newChildDuration,
      })
    );
    // TODO: Remove the possibility to create session blocks when opening the modal
  };

  const onDelete = async (e: MouseEvent) => {
    e.stopPropagation();

    const deleteEntry = {
      [EntryType.Break]: () => dispatch(actions.deleteBreak(entry, eventId)),
      [EntryType.SessionBlock]: () => dispatch(actions.deleteBlock(entry, eventId)),
      [EntryType.Contribution]: () => dispatch(actions.unscheduleEntry(entry, eventId)),
    }[entry.type];

    deleteEntry();
    onClose();
  };

  const locationArray = _getOrderedLocationArray();
  let presenters, fileCount;
  if (type !== EntryType.Break) {
    presenters = _getPresentersArray();
    fileCount = _getFileCount();
  }

  return (
    <Card fluid style={{minWidth: 400, boxShadow: 'none'}}>
      <Card.Content>
        <Card.Header>
          <div style={{display: 'flex', justifyContent: 'flex-end', gap: 5}}>
            <ButtonGroup>
              <Button icon="edit" onClick={onEdit} />
              {/* TODO: (Ajob) Evaluate if we actually need the button below */}
              {/* <Button icon="paint brush" /> */}
              {type === EntryType.Contribution ? (
                <Popup
                  content={<Translate>Unschedule contribution</Translate>}
                  inverted
                  size="mini"
                  position="bottom center"
                  trigger={<Button icon="calendar times" onClick={onDelete} color="orange" />}
                />
              ) : (
                <Button icon="trash" onClick={onDelete} />
              )}
              {type === EntryType.SessionBlock && (
                <>
                  <Popup
                    content={<Translate>Add new Contribution/Break</Translate>}
                    size="mini"
                    trigger={<Button icon="plus" onClick={onCreateChild} color="green" />}
                  />
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
                </>
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
            <div>
              {type === EntryType.SessionBlock ? formatBlockTitle(sessionTitle, title) : title}
            </div>
          </div>
        </Card.Header>
        <CardItem icon="clock outline">{formatTimeRange('en', startTime, endTime)}</CardItem>
        {locationArray.length ? (
          <CardItem icon="map marker alternate">
            <List style={{textAlign: 'left', marginTop: 0}}>
              {locationArray.map((v: string, i) => (
                <List.Item color="red" key={i}>
                  {v}
                </List.Item>
              ))}
            </List>
          </CardItem>
        ) : null}
        {presenters && presenters.length ? (
          <CardItem icon="microphone">
            {presenters.join(', ') || Translate.string('No presenters')}
          </CardItem>
        ) : null}
        {fileCount ? (
          <CardItem icon="file outline">
            <PluralTranslate count={fileCount}>
              <Singular>
                <Param name="count" value={fileCount} /> file
              </Singular>
              <Plural>
                <Param name="count" value={fileCount} /> files
              </Plural>
            </PluralTranslate>
          </CardItem>
        ) : null}
      </Card.Content>
    </Card>
  );
}

export function EntryPopup({
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
      <EntryPopupContent entry={entry} onClose={onClose} />
    </Popup>
  );
}
