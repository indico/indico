// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {Header, Modal, Button, List, Message, Divider} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

interface PublicationModalProps {
  open: boolean;
  setModalOpen: (open: boolean) => void;
  trigger: React.ReactNode;
  published: boolean;
  onClick: () => void;
}

export default function PublicationModal({
  open,
  setModalOpen,
  trigger,
  published,
  onClick,
}: PublicationModalProps) {
  return (
    <Modal open={open} onClose={() => setModalOpen(false)} size="tiny" trigger={trigger} closeIcon>
      <Header
        content={
          published
            ? Translate.string('Set contribution list in draft mode')
            : Translate.string('Publish contributions')
        }
      />
      <Modal.Content>
        <Header as="h4">
          <Translate>Are you sure?</Translate>
        </Header>
        <p>
          {published ? (
            <Translate>
              The following menu items will not be accessible to event participants.
            </Translate>
          ) : (
            <Translate>
              The following menu items will be accessible to event participants.
            </Translate>
          )}
        </p>
        <Message warning>
          <List bulleted>
            <List.Item>
              <Translate>Contribution List</Translate>
            </List.Item>
            <List.Item>
              <Translate>My Contributions</Translate>
            </List.Item>
            <List.Item>
              <Translate>Author List</Translate>
            </List.Item>
            <List.Item>
              <Translate>Speaker List</Translate>
            </List.Item>
            <List.Item>
              <Translate>Timetable</Translate>
            </List.Item>
            <List.Item>
              <Translate>Book of Abstracts</Translate>
            </List.Item>
          </List>
        </Message>
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={() => setModalOpen(false)}>
          <Translate>Cancel</Translate>
        </Button>
        <Button primary onClick={onClick}>
          <Translate>Confirm</Translate>
        </Button>
      </Modal.Actions>
    </Modal>
  );
}
