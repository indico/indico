// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import publicationURL from 'indico-url:contributions.manage_publication';

import React, {useState} from 'react';
import {Button, Icon} from 'semantic-ui-react';

import {useTogglableValue} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

import PublicationModal from './PublicationModal';

interface PublicationStateSwitch {
  eventId: string;
  onSuccess?: () => void;
  [key: string]: any;
}

export default function PublicationStateSwitch({
  eventId,
  onSuccess = () => undefined,
  ...rest
}: PublicationStateSwitch) {
  const url = publicationURL({event_id: eventId});
  const [modalOpen, setModalOpen] = useState(false);

  const [published, togglePublished, loading] = useTogglableValue(
    publicationURL({event_id: eventId})
  );

  if (loading) {
    return null;
  }

  const onClick = async () => {
    try {
      await indicoAxios.put(url);
    } catch (error) {
      return handleAxiosError(error);
    }

    togglePublished();
    onSuccess();
    setModalOpen(false);
  };

  const trigger = (
    <Button
      onClick={() => setModalOpen(true)}
      title={
        published
          ? Translate.string('Unpublish timetable and contributions to event participants')
          : Translate.string('Publish timetable and contributions to event participants')
      }
      color={published ? 'green' : null}
      {...rest}
    >
      <Icon name={published ? 'lock open' : 'lock'} />
      {published ? <Translate>Published</Translate> : <Translate>Unpublished</Translate>}
    </Button>
  );

  return (
    <PublicationModal
      open={modalOpen}
      setModalOpen={setModalOpen}
      trigger={trigger}
      published={published}
      onClick={onClick}
    />
  );
}
