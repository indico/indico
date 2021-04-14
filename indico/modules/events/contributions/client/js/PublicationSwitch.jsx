// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import publicationURL from 'indico-url:contributions.manage_publication';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Header, Modal, Button, Checkbox, List} from 'semantic-ui-react';

import {useTogglableValue} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

export default function PublicationSwitch({eventId}) {
  const [modalOpen, setModalOpen] = useState(false);

  const [published, togglePublished, loading, saving] = useTogglableValue(
    publicationURL({event_id: eventId})
  );

  if (loading) {
    return null;
  }

  return (
    <Modal
      open={modalOpen}
      onClose={() => setModalOpen(false)}
      size="tiny"
      trigger={
        <Checkbox
          label={published ? Translate.string('Published') : Translate.string('Draft')}
          toggle
          onClick={() => setModalOpen(true)}
          checked={published}
          disabled={saving}
        />
      }
      closeIcon
    >
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
        <Button
          primary
          onClick={() => {
            togglePublished();
            setModalOpen(false);
          }}
        >
          <Translate>Yes</Translate>
        </Button>
      </Modal.Actions>
    </Modal>
  );
}

PublicationSwitch.propTypes = {
  eventId: PropTypes.string.isRequired,
};
