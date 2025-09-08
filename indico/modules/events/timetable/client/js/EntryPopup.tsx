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
import {Button, Card, Icon, List, Popup, Label, Header, PopupProps} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import './Entry.module.scss';
import {indicoAxios} from 'indico/utils/axios';

import * as actions from './actions';
import {formatTimeRange} from './i18n';
import {ReduxState} from './reducers';
import * as selectors from './selectors';
import {BreakEntry, ContribEntry, BlockEntry, EntryType, PersonLinkRole} from './types';
import {mapTTDataToEntry} from './utils';

function ActionPopup({content, trigger, ...rest}: PopupProps) {
  return (
    <Popup
      inverted
      size="mini"
      position="bottom center"
      content={content}
      trigger={trigger}
      {...rest}
    />
  );
}

function EntryPopupContent({entry, onClose}: {entry; onClose: () => void}) {
  const dispatch = useDispatch();
  const {type, title, attachments = [], parent: entryParent, colors = {}} = entry;
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
          {entryParent && session && (
            <Label
              circular
              title={Translate.string('Session title')}
              styleName="session"
              size="tiny"
              style={{...entryParent.colors}}
            >
              <Translate>{session.title}</Translate>
            </Label>
          )}
          <Header as="h5" color={!title ? 'grey' : null}>
            <span>
              <Label circular size="tiny" styleName="header-accent" style={{...colors}} />
              <span>{title || Translate.string('No title')}</span>
            </span>
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
          <List.Item title={Translate.string('Date and time')}>
            <Icon name="clock outline" />
            {formatTimeRange('en', startTime, endTime)}
          </List.Item>
          {entryParent?.title && (
            <List.Item title={Translate.string('Session block title')}>
              <Icon name="calendar alternate outline" />
              <Label circular basic styleName="session">
                {entryParent.title}
              </Label>
            </List.Item>
          )}
          {locationArray.length ? (
            <List.Item title={Translate.string('Location')} style={{display: 'flex'}}>
              <Icon name="map outline" />
              <p>{locationArray.join(', ')}</p>
            </List.Item>
          ) : null}
          {presenters?.length ? (
            <List.Item title={Translate.string('Presenters')}>
              <Icon name="user outline" />
              <List styleName="inline">
                {presenters.map(p => {
                  return (
                    <List.Item key={p.email}>
                      <Label image>
                        <img src={p.avatarURL} />
                        <span>{p.name}</span>
                      </Label>
                    </List.Item>
                  );
                })}
              </List>
            </List.Item>
          ) : null}
          {attachments.length ? (
            <List.Item title={Translate.string('Attachments')}>
              <Icon name="copy outline" />
              <List styleName="inline">
                {attachments.map(a => {
                  const iconName = {
                    attachment: 'file',
                    folder: 'folder',
                  }[a.type];

                  return (
                    <List.Item key={a.id}>
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
      <Card.Content styleName="actions" textAlign="right">
        {type === EntryType.SessionBlock && (
          <>
            {/* TODO: (Ajob) Evaluate this feature */}
            <ActionPopup
              content={<Translate>Edit session protection</Translate>}
              trigger={<Button disabled basic icon="shield" />}
            />
            {/* TODO: (Ajob) Evaluate this feature */}
            <ActionPopup
              content={<Translate>Edit session</Translate>}
              trigger={<Button disabled basic icon="calendar alternate outline" />}
            />
            <ActionPopup
              content={<Translate>Add new child</Translate>}
              trigger={<Button basic icon="plus" onClick={onCreateChild} />}
            />
          </>
        )}
        <ActionPopup
          content={Translate.string('Edit')}
          trigger={<Button basic icon="edit" onClick={onEdit} />}
        />
        {type === EntryType.Contribution ? (
          <ActionPopup
            content={<Translate>Unschedule contribution</Translate>}
            trigger={<Button basic icon="calendar times" onClick={onDelete} />}
          />
        ) : (
          <ActionPopup
            content={Translate.string('Delete')}
            trigger={
              <Button basic title={Translate.string('Delete')} icon="trash" onClick={onDelete} />
            }
          />
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
      position="top left"
      onClose={onClose}
      basic
      hideOnScroll
      styleName="wrapper"
    >
      <EntryPopupContent entry={entry} onClose={onClose} />
    </Popup>
  );
}
