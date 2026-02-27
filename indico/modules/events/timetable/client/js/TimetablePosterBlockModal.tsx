// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import contributionURL from 'indico-url:timetable.tt_contrib_rest';

import React from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {ThunkDispatch} from 'redux-thunk';
import {Button, Label, Modal, Segment} from 'semantic-ui-react';

import {Param, Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import * as actions from './actions';
import {DRAFT_ENTRY_MODAL, POSTER_BLOCK_CONTRIBUTIONS_MODAL, useModal} from './ModalContext';
import * as selectors from './selectors';
import {BlockEntry, ContribEntry, EntryType, ReduxState, Session, SessionBlockId} from './types';
import {mapTTDataToEntry} from './utils';

import './TimetablePosterBlockModal.module.scss';

interface TimetablePosterBlockModalProps {
  id: SessionBlockId;
  onClose: () => void;
}

interface PosterContributionProps {
  entry: ContribEntry;
  block: BlockEntry;
  session: Session;
}

const PosterContribution: React.FC<PosterContributionProps> = ({entry, block, session}) => {
  const dispatch: ThunkDispatch<ReduxState, unknown, actions.Action> = useDispatch();
  const {openModal} = useModal();
  const eventId = useSelector(selectors.getEventId);

  const onEdit = async e => {
    e.stopPropagation();
    const editURL = contributionURL({event_id: eventId, contrib_id: entry.objId});
    const {data} = await indicoAxios.get(editURL);
    data.type = EntryType.Contribution;

    const sessions = session ? {[session.id]: session} : {};
    const draftEntry = mapTTDataToEntry(data, sessions);
    dispatch(actions.setDraftEntry(draftEntry));
    openModal(DRAFT_ENTRY_MODAL, {
      eventId,
      entry: draftEntry,
      onClose: () => {
        dispatch(actions.setDraftEntry(null));
        openModal(POSTER_BLOCK_CONTRIBUTIONS_MODAL, {id: block.id});
      },
    });
  };

  const onDelete = async () => {
    dispatch(actions.unscheduleEntry(entry, eventId));
  };

  return (
    <Segment styleName="contrib">
      {entry.title}
      <div>
        <Button
          type="button"
          icon="edit"
          title={Translate.string('Edit')}
          basic
          size="small"
          onClick={onEdit}
        />
        <Button
          type="button"
          icon="trash"
          title={Translate.string('Delete')}
          basic
          size="small"
          onClick={onDelete}
        />
      </div>
    </Segment>
  );
};

export const TimetablePosterBlockModal: React.FC<TimetablePosterBlockModalProps> = ({
  id,
  onClose,
}) => {
  const dispatch: ThunkDispatch<ReduxState, unknown, actions.Action> = useDispatch();
  const {openModal} = useModal();
  const eventId = useSelector(selectors.getEventId);
  const block = useSelector(selectors.getCurrentDayEntries).find(
    (e): e is BlockEntry => e.id === id
  );
  const session = useSelector((state: ReduxState) =>
    selectors.getSessionById(state, block.sessionId)
  );

  const onCreate = () => {
    const draftEntry = {
      sessionId: session.id,
      sessionBlockId: block.objId,
      duration: Math.min(20, block.duration),
      startDt: block.startDt,
    };
    actions.setDraftEntry(draftEntry);
    openModal(DRAFT_ENTRY_MODAL, {
      eventId,
      entry: draftEntry,
      onClose: () => {
        dispatch(actions.setDraftEntry(null));
        openModal(POSTER_BLOCK_CONTRIBUTIONS_MODAL, {id: block.id});
      },
    });
  };

  if (!(block || session)) {
    return;
  }

  const children = block.children.sort((c1, c2) => c1.title.localeCompare(c2.title));

  return (
    <Modal size="small" onClose={onClose} defaultOpen closeIcon>
      <Modal.Header styleName="title">
        <Label circular size="mini" style={session.colors} />
        <Translate>
          Contributions of '
          <Param name="posterSessionBlockTitle" value={block.title} />'
        </Translate>
      </Modal.Header>
      <Modal.Content styleName="modal-content">
        <Segment.Group styleName="contribs">
          {children.map(c => (
            <PosterContribution
              key={c.id}
              entry={c as ContribEntry}
              block={block}
              session={session}
            />
          ))}
        </Segment.Group>
      </Modal.Content>
      <Modal.Actions>
        <Button
          onClick={onCreate}
          primary
          basic
          floated="left"
          icon="plus"
          content={Translate.string('Create contribution')}
        />
        <Button onClick={onClose} content={Translate.string('Close')} />
      </Modal.Actions>
    </Modal>
  );
};
