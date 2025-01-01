// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Header, Modal, Button, List} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

export default function PublicationModal({open, setModalOpen, trigger, published, onClick}) {
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
        {published ? (
          <>
            <p>
              <Translate>
                Are you sure you want to change the contribution list back to draft mode?
              </Translate>
            </p>
            <p>
              <Translate>By doing so the following menu items won't be accessible:</Translate>
            </p>
          </>
        ) : (
          <>
            <p>
              <Translate>Are you sure you want to publish the contribution list?</Translate>
            </p>
            <p>
              <Translate>By doing so the following menu items will be accessible:</Translate>
            </p>
          </>
        )}
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
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={() => setModalOpen(false)}>
          <Translate>No</Translate>
        </Button>
        <Button primary onClick={onClick}>
          <Translate>Yes</Translate>
        </Button>
      </Modal.Actions>
    </Modal>
  );
}

PublicationModal.propTypes = {
  open: PropTypes.bool.isRequired,
  setModalOpen: PropTypes.func.isRequired,
  trigger: PropTypes.node.isRequired,
  published: PropTypes.bool.isRequired,
  onClick: PropTypes.func.isRequired,
};
