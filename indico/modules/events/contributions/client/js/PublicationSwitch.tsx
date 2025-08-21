// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import publicationURL from 'indico-url:contributions.manage_publication';

import React, {useState} from 'react';

import {Checkbox} from 'indico/react/components';
import {useTogglableValue} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

import PublicationModal from './PublicationModal';

export default function PublicationSwitch({eventId}: {eventId: string}) {
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
      showAsToggle
      onChange={() => setModalOpen(true)}
      checked={published}
      disabled={saving}
      indeterminate={false}
      className={null}
      style={null}
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
