// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Dimmer, Loader} from 'semantic-ui-react';

import {handleSubmitError} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import {FinalTextEditor} from '../TextEditor';

export function NoteEditor({apiURL, imageUploadURL, closeModal, getNoteURL}) {
  const [currentInput, setCurrentInput] = useState(undefined);
  const [loading, setLoading] = useState(false);
  const [allowWithoutChange, setAllowWithoutChange] = useState(false);

  const getNote = async () => {
    let resp;
    try {
      resp = await indicoAxios.get(getNoteURL || apiURL);
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    if (resp.data.source) {
      setCurrentInput(resp.data.source);
    } else if (resp.data.notes) {
      setCurrentInput(
        resp.data.notes
          .map(note => `<h1>● ${_.escape(note.object_title)}</h1>\n${note.html}`)
          .join('\n<hr>\n')
      );
      setAllowWithoutChange(true);
    } else {
      setCurrentInput('');
    }
    setLoading(false);
  };

  const handleSubmit = async data => {
    try {
      if (!data.source) {
        await indicoAxios.delete(apiURL);
      } else {
        await indicoAxios.post(apiURL, {
          source: data.source,
          render_mode: 'html',
        });
      }
    } catch (e) {
      return handleSubmitError(e);
    }
    setCurrentInput(data.source);
    setTimeout(() => location.reload(), 10);
    // never finish submitting to avoid fields being re-enabled
    await new Promise(() => {});
  };

  if (currentInput === undefined && !loading) {
    setLoading(true);
    getNote();
  }

  return (
    <>
      <Dimmer active={loading} page>
        <Loader active />
      </Dimmer>
      {!loading && currentInput !== undefined && (
        <FinalModalForm
          id="edit-minutes"
          header={Translate.string('Edit Minutes')}
          submitLabel={Translate.string('Save')}
          size="large"
          initialValues={{source: currentInput}}
          onClose={closeModal}
          onSubmit={handleSubmit}
          disabledUntilChange={!allowWithoutChange}
          unloadPrompt
        >
          <FinalTextEditor
            name="source"
            loading={loading}
            value={currentInput}
            parse={v => v}
            config={{images: true, imageUploadURL}}
          />
        </FinalModalForm>
      )}
    </>
  );
}

NoteEditor.propTypes = {
  apiURL: PropTypes.string.isRequired,
  imageUploadURL: PropTypes.string.isRequired,
  closeModal: PropTypes.func.isRequired,
  getNoteURL: PropTypes.string,
};

NoteEditor.defaultProps = {
  getNoteURL: null,
};
