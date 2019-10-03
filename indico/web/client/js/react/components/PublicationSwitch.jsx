// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import publicationURL from 'indico-url:contributions.manage_publication';

import React, {useState, useEffect} from 'react';
import PropTypes from 'prop-types';
import {Header, Modal, Button, Checkbox, List} from 'semantic-ui-react';
import indicoAxios, {handleAxiosError} from 'indico/utils/axios';
import {Translate} from 'indico/react/i18n';

export default function PublicationSwitch({confId}) {
  const [published, setPublished] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    const fetchPublicationSetting = async () => {
      let response;
      try {
        response = await indicoAxios.get(publicationURL({confId}));
        setPublished(response.data.published);
      } catch (error) {
        handleAxiosError(error);
      }
    };
    fetchPublicationSetting();
  }, [confId]);

  const publish = shouldPublish => {
    const updatePublicationSetting = async () => {
      try {
        if (shouldPublish) {
          await indicoAxios.put(publicationURL({confId}));
        } else {
          await indicoAxios.delete(publicationURL({confId}));
        }
        setPublished(shouldPublish);
      } catch (error) {
        handleAxiosError(error);
      }
    };
    updatePublicationSetting();
  };

  const menuList = (
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
  );

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
        />
      }
      closeIcon
    >
      <Header
        content={
          !published
            ? Translate.string('Publish Contributions')
            : Translate.string('Set contribution list in Draft mode')
        }
      />
      <Modal.Content>
        {published ? (
          <>
            <p>
              <Translate>Are you sure you want to set contribution list in draft mode?</Translate>
            </p>
            <p>
              <Translate>By doing so the following menu items won't be accessible:</Translate>
            </p>
            {menuList}
          </>
        ) : (
          <>
            <p>
              <Translate>Are you sure you want to publish the contribution list?</Translate>
            </p>
            <p>
              <Translate>By doing so the following menu items will be accessible: </Translate>
            </p>
            {menuList}
          </>
        )}
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={() => setModalOpen(false)}>
          <Translate>No</Translate>
        </Button>
        <Button
          color="blue"
          onClick={() => {
            publish(!published);
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
  confId: PropTypes.number.isRequired,
};
