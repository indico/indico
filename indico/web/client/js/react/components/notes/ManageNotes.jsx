// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
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

export default function ManageNotes({icon, title, apiURL, imageUploadURL, getNoteURL, modalTitle}) {
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
            href=""
            className="i-link icon-edit"
            title={Translate.string('Edit minutes')}
            onClick={evt => {
              evt.preventDefault();
              setModalOpen(true);
            }}
          />{' '}
          <a
            href=""
            className="i-link icon-remove"
            title={Translate.string('Delete minutes')}
            onClick={evt => {
              evt.preventDefault();
              setIsDeleting(true);
            }}
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
        <a
          href=""
          onClick={evt => {
            evt.preventDefault();
            setModalOpen(true);
          }}
        >
          {title}
        </a>
      )}
      {modalOpen && (
        <NoteEditor
          apiURL={apiURL}
          imageUploadURL={imageUploadURL}
          closeModal={saved => {
            if (saved) {
              location.reload();
            } else {
              setModalOpen(false);
            }
          }}
          getNoteURL={getNoteURL}
          modalTitle={modalTitle}
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
  modalTitle: PropTypes.string.isRequired,
};

ManageNotes.defaultProps = {
  icon: true,
  title: '',
  getNoteURL: null,
};
