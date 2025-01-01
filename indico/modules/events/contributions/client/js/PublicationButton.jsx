// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import publicationURL from 'indico-url:contributions.manage_publication';

import PropTypes from 'prop-types';
import React, {useState} from 'react';

import {IButton} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

import PublicationModal from './PublicationModal';

export default function PublicationButton({eventId, onSuccess}) {
  const url = publicationURL({event_id: eventId});
  const [modalOpen, setModalOpen] = useState(false);

  const onClick = async () => {
    try {
      await indicoAxios.put(url);
    } catch (error) {
      return handleAxiosError(error);
    }
    onSuccess();
    setModalOpen(false);
  };

  const trigger = (
    <IButton onClick={() => setModalOpen(true)}>
      <Translate>Publish contributions</Translate>
    </IButton>
  );

  return (
    <PublicationModal
      open={modalOpen}
      setModalOpen={setModalOpen}
      trigger={trigger}
      published={false}
      onClick={onClick}
    />
  );
}

PublicationButton.propTypes = {
  eventId: PropTypes.string.isRequired,
  onSuccess: PropTypes.func.isRequired,
};
