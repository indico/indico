// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import publicationURL from 'indico-url:contributions.manage_publication';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Checkbox} from 'semantic-ui-react';

import {useTogglableValue} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

import PublicationModal from './PublicationModal';

export default function PublicationSwitch({eventId}) {
  const [modalOpen, setModalOpen] = useState(false);

  const [published, togglePublished, loading, saving] = useTogglableValue(
    publicationURL({event_id: eventId})
  );

  if (loading) {
    return null;
  }

  const trigger = (
    <Checkbox
      label={published ? Translate.string('Published') : Translate.string('Draft')}
      toggle
      onClick={() => setModalOpen(true)}
      checked={published}
      disabled={saving}
    />
  );

  return (
    <PublicationModal
      open={modalOpen}
      setModalOpen={setModalOpen}
      trigger={trigger}
      published={published}
      onClick={() => {
        togglePublished();
        setModalOpen(false);
      }}
    />
  );
}

PublicationSwitch.propTypes = {
  eventId: PropTypes.string.isRequired,
};
