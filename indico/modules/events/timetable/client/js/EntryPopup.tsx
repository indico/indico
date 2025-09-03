// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-nocheck

import breakURL from 'indico-url:timetable.tt_break_rest';
import contributionURL from 'indico-url:timetable.tt_contrib_rest';
import sessionBlockURL from 'indico-url:timetable.tt_session_block_rest';

import './EntryPopup.module.scss';
import moment from 'moment';
import React from 'react';
import {useSelector, useDispatch} from 'react-redux';
import {
  Button,
  Card,
  Dropdown,
  DropdownItem,
  DropdownMenu,
  Icon,
  List,
  Popup,
  Label,
  Header,
} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import './Entry.module.scss';
import {indicoAxios} from 'indico/utils/axios';

import * as actions from './actions';
import {formatTimeRange} from './i18n';
import {ReduxState} from './reducers';
import * as selectors from './selectors';
import {BreakEntry, ContribEntry, BlockEntry, EntryType, PersonLinkRole} from './types';
import {mapTTDataToEntry} from './utils';

function EntryPopupContent({entry, onClose}: {entry; onClose: () => void}) {
  const dispatch = useDispatch();
  const {type, title, attachments = [], sessionTitle, colors} = entry;
  const sessions = useSelector(selectors.getSessions);
  const session = useSelector((state: ReduxState) =>
    selectors.getSessionById(state, entry.sessionId)
  );

  const eventId = useSelector(selectors.getEventId);
  const startTime = moment(entry.startDt);
  const endTime = moment(entry.startDt).add(entry.duration, 'minutes');

  const _getOrderedLocationArray = () => {
    const {locationData = {}} = entry;
    const {address, venueName, roomName} = locationData;
    return Object.values([address, venueName, roomName]).filter(Boolean);
  };

  const _getPresentersArray = () => {
    const {personLinks = []} = entry;
    return personLinks.filter(p => !p.roles || p.roles.includes(PersonLinkRole.SPEAKER));
  };

  const onEdit = async () => {
    const {objId} = entry;
    if (!objId) {
      return;
    }

    const editURL = {
      [EntryType.Contribution]: contributionURL({event_id: eventId, contrib_id: objId}),
      [EntryType.SessionBlock]: sessionBlockURL({event_id: eventId, session_block_id: objId}),
      [EntryType.Break]: breakURL({event_id: eventId, break_id: objId}),
    }[type];

    const {data} = await indicoAxios.get(editURL);
    data['type'] = type;

    const sessions = session ? {[session.id]: session} : {};
    const draftEntry = mapTTDataToEntry(data, sessions);

    if (entry.type === EntryType.SessionBlock) {
      draftEntry.children = entry.children;
    }

    dispatch(actions.setDraftEntry(draftEntry));
    onClose();
  };

  const onCreateChild = async (e: MouseEvent) => {
    e.stopPropagation();
    onClose();
    let newChildStartDt = moment(entry.startDt);
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
    const newChildDuration = session.defaultContribDurationMinutes;
    // TODO: (Michel) Disable time picker for any time after parent end time
    dispatch(
      actions.setDraftEntry({
        startDt: newChildStartDt,
        duration: newChildDuration,
        sessionBlockId: entry.objId,
        sessionId: entry.sessionId,
        locationParent: entry.childLocationParent,
        locationData: {...entry.childLocationParent.location_data, inheriting: true},
      })
    );
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
  let presenters;
  if (type !== EntryType.Break) {
    presenters = _getPresentersArray();
  }

  return (
    <>
      <div styleName="header-wrapper">
        <div styleName="header-wrapper-content">
          {session && (
            <Label circular styleName="session" size="tiny" style={{...colors}}>
              <Translate>{session.title}</Translate>
            </Label>
          )}
          <Header as="h5">
            {/* <Icon style={{...colors}} name={getIconByEntryType(type)}/> */}
            {!session && <div styleName="header-accent" style={{...colors}} />}
            {title}
          </Header>
        </div>
        <Button
          basic
          icon="close"
          styleName="close"
          onClick={e => {
            e.stopPropagation();
            onClose();
          }}
        />
      </div>
      <Card.Content styleName="main">
        <List styleName="main-list">
          <List.Item>
            <Icon name="clock outline" />
            {formatTimeRange('en', startTime, endTime)}
          </List.Item>
          {locationArray.length ? (
            <List.Item style={{display: 'flex'}}>
              <Icon name="map outline" />
              <p>{locationArray.join(', ')}</p>
            </List.Item>
          ) : null}
          {presenters?.length ? (
            <List.Item>
              <Icon name="user outline" />
              <List>
                {presenters.map(p => {
                  return (
                    <List.Item key={p.email}>
                      <Label image>
                        <img src={p.avatarURL} />
                        {p.name}
                      </Label>
                    </List.Item>
                  );
                })}
              </List>
            </List.Item>
          ) : null}
          {attachments.length ? (
            <List.Item>
              <Icon name="copy outline" />
              <List styleName="inline">
                {attachments.map(a => {
                  const iconName = {
                    attachment: 'file',
                    folder: 'folder',
                  }[a.type];

                  return (
                    <List.Item>
                      <Label
                        style={{fontWeight: 'normal'}}
                        basic
                        key={a.id}
                        icon={iconName}
                        content={a.title}
                      />
                    </List.Item>
                  );
                })}
              </List>
            </List.Item>
          ) : null}
        </List>
      </Card.Content>
      <Card.Content textAlign="right">
        <Button basic icon="edit" onClick={onEdit} />
        {type === EntryType.Contribution ? (
          <Popup
            content={<Translate>Unschedule contribution</Translate>}
            inverted
            size="mini"
            position="bottom center"
            trigger={<Button basic icon="calendar times" onClick={onDelete} />}
          />
        ) : (
          <Button icon="trash" onClick={onDelete} />
        )}
        {type === EntryType.SessionBlock && (
          <>
            <Popup
              content={<Translate>Add new child</Translate>}
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
      </Card.Content>
    </>
  );
}

export function EntryPopup({
  trigger,
  onClose,
  entry,
  open = false,
}: {
  trigger: React.ReactNode;
  onClose: () => void;
  entry: BreakEntry | ContribEntry | BlockEntry;
  open?: boolean;
}) {
  return (
    <Popup
      trigger={trigger}
      on="click"
      open={open}
      position="top center"
      onClose={onClose}
      basic
      hideOnScroll
      wide
      styleName="wrapper"
    >
      <EntryPopupContent entry={entry} onClose={onClose} />
    </Popup>
  );
}
