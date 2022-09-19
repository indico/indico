// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';

import {RequestConfirmDelete} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import {NoteEditor} from './NoteEditor';

export default function ManageNotes({icon, title, apiURL, imageUploadURL, getNoteURL}) {
  const [modalOpen, setModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    try {
      await indicoAxios.delete(apiURL);
    } catch (e) {
      handleAxiosError(e);
      return;
    }
    location.reload();
  };

  return (
    <>
      {icon ? (
        <>
          <a
            className="i-link icon-edit"
            title={Translate.string('Edit minutes')}
            onClick={() => setModalOpen(true)}
          />{' '}
          <a
            className="i-link icon-remove"
            title={Translate.string('Delete minutes')}
            onClick={() => setIsDeleting(true)}
          />
          <RequestConfirmDelete
            onClose={() => setIsDeleting(false)}
            requestFunc={handleDelete}
            open={isDeleting}
          >
            <Translate>Are you sure you want to delete these minutes?</Translate>
          </RequestConfirmDelete>
        </>
      ) : (
        <a onClick={() => setModalOpen(true)}>{title}</a>
      )}
      {modalOpen && (
        <NoteEditor
          apiURL={apiURL}
          imageUploadURL={imageUploadURL}
          closeModal={() => setModalOpen(false)}
          getNoteURL={getNoteURL}
        />
      )}
    </>
  );
}

ManageNotes.propTypes = {
  icon: PropTypes.bool,
  title: PropTypes.string,
  apiURL: PropTypes.string.isRequired,
  imageUploadURL: PropTypes.string.isRequired,
  getNoteURL: PropTypes.string,
};

ManageNotes.defaultProps = {
  icon: true,
  title: '',
  getNoteURL: null,
};
