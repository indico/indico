// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import renderMarkdownURL from 'indico-url:core.markdown';
import userPreferencesMarkdownAPI from 'indico-url:users.user_preferences_markdown_api';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState, useEffect, useCallback} from 'react';
import {Field} from 'react-final-form';
import {Dimmer, Loader} from 'semantic-ui-react';

import {ConfirmButton} from 'indico/react/components';
import {handleSubmitError} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';
import {injectModal} from 'indico/react/util';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';

import {FinalMarkdownEditor} from '../MarkdownEditor';
import {FinalTinyMCETextEditor} from '../TinyMCETextEditor';

import {ConflictModal} from './ConflictModal';

import 'react-markdown-editor-lite/lib/index.css';

export function NoteEditor({apiURL, imageUploadURL, closeModal, getNoteURL, modalTitle}) {
  const [currentInput, setCurrentInput] = useState(undefined);
  const [loading, setLoading] = useState(false);
  const [allowWithoutChange, setAllowWithoutChange] = useState(false);
  const [converting, setConverting] = useState(false);
  const [shouldReloadPage, setShouldReloadPage] = useState(false);
  const [renderMode, setRenderMode] = useState(undefined);
  const [closeAndReload, setCloseAndReload] = useState(false);
  const [currentNoteRevision, setCurrentNoteRevision] = useState(null);

  const combineNotes = (resp, mode) => {
    if (mode === 'markdown') {
      setCurrentInput(
        resp.data.notes
          .map(note => `# ● ${_.escape(note.objectTitle)}\n${note.source}`)
          .join('\n\n---\n\n')
      );
    } else {
      setCurrentInput(
        resp.data.notes
          .map(note => `<h1>● ${_.escape(note.objectTitle)}</h1>\n${note.html}`)
          .join('\n<hr>\n')
      );
    }
    setAllowWithoutChange(true);
  };

  const getUserPreferences = async () => {
    let resp;
    try {
      resp = await indicoAxios.get(userPreferencesMarkdownAPI());
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    const mode = resp.data ? 'markdown' : 'html';
    setRenderMode(mode);
    setLoading(false);
    return mode;
  };

  const getNote = useCallback(async () => {
    let resp;
    try {
      resp = await indicoAxios.get(getNoteURL || apiURL);
      resp = camelizeKeys(resp);
      setCurrentNoteRevision(resp.data);
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    if (resp.data.source) {
      // in case we only edit minutes:
      setCurrentInput(resp.data.source);
      if (resp.data.renderMode) {
        // in this case we should always get the render mode anyway, so this might not be needed
        setRenderMode(resp.data.renderMode);
        setLoading(false);
      } else {
        getUserPreferences();
      }
    } else if (resp.data.notes) {
      // in case we compile minutes:
      if (resp.data.notes.every(n => n.renderMode === 'markdown')) {
        // we will use markdown for compiling exactly for one case:
        // all minutes are markdown and the user has a preference for writing minutes in markdown
        const mode = await getUserPreferences();
        combineNotes(resp, mode);
      } else {
        // in all other cases we want to use html
        combineNotes(resp, 'html');
        setRenderMode('html');
      }
      setLoading(false);
    } else {
      // in case we create new minutes:
      setCurrentInput('');
      getUserPreferences();
    }
  }, [getNoteURL, apiURL, setCurrentNoteRevision]);

  const handleSubmit = async ({source, forceRevision}) => {
    // getData is currently unused, keeping it around in case we need to enable lazyValue
    // for the TinyMCE editor widget in case larger notes cause performance issues that
    // can be resolved by only rendering them to an html string at submission time
    const currentValue = source.getData ? source.getData() : source;
    try {
      if (!currentValue) {
        await indicoAxios.delete(apiURL);
      } else {
        const resp = await indicoAxios.post(apiURL, {
          source: currentValue,
          render_mode: renderMode,
          revision_id: forceRevision || currentNoteRevision.id,
        });
        setCurrentNoteRevision(resp.data);
      }
    } catch (e) {
      if (_.get(e, 'response.status') !== 418) {
        return handleSubmitError(e);
      }
      // handle note conflict
      const conflictData = camelizeKeys(e.response.data);
      const resolution = await injectModal(resolve => (
        <ConflictModal data={conflictData} onClose={action => resolve(action)} />
      ));
      setShouldReloadPage(true); // we know something changed outside -> reload page on dialog close
      if (resolution === 'overwrite') {
        return await handleSubmit({
          source: currentValue,
          forceRevision: e.response.data.conflict.id,
        });
      } else if (resolution === 'discard') {
        setRenderMode(e.response.data.conflict.render_mode);
        setCurrentInput(e.response.data.conflict.source);
        setCurrentNoteRevision(conflictData.conflict);
      }
      return;
    }
    setCurrentInput(source);
    setShouldReloadPage(true);
  };

  const convertToHTML = markdownSource => async () => {
    setConverting(true);
    let resp;
    try {
      resp = await indicoAxios.post(renderMarkdownURL(), {source: markdownSource});
    } catch (e) {
      handleAxiosError(e);
      return;
    }
    setRenderMode('html');
    setCurrentInput(resp.data.html);
  };

  useEffect(() => {
    setLoading(true);
    getNote();
  }, [getNote]);

  useEffect(() => {
    if (closeAndReload) {
      closeModal(true);
    }
  }, [closeAndReload, closeModal]);

  return (
    <>
      <Dimmer active={loading || closeAndReload} page>
        <Loader active />
      </Dimmer>
      {!loading && !closeAndReload && currentInput !== undefined && (
        <FinalModalForm
          id="edit-minutes"
          header={modalTitle}
          submitLabel={Translate.string('Save')}
          style={{minWidth: '65vw'}}
          size="large"
          initialValues={{source: currentInput}}
          onClose={() => (shouldReloadPage ? setCloseAndReload(true) : closeModal(false))}
          onSubmit={handleSubmit}
          disabledUntilChange={!allowWithoutChange}
          unloadPrompt
          extraActions={fprops =>
            renderMode === 'markdown' && (
              <Field name="source" subscription={{value: true}}>
                {({input: {value: markdownSource}}) => (
                  <ConfirmButton
                    style={{marginRight: 'auto'}}
                    onClick={convertToHTML(markdownSource)}
                    disabled={fprops.submitting || converting}
                    basic
                    popupContent={Translate.string(
                      'You cannot switch back to Markdown after switching to HTML.'
                    )}
                  >
                    <Translate>Use rich-text (HTML) editor</Translate>
                  </ConfirmButton>
                )}
              </Field>
            )
          }
        >
          {renderMode === 'markdown' && (
            <FinalMarkdownEditor name="source" imageUploadURL={imageUploadURL} height="70vh" />
          )}
          {renderMode === 'html' && (
            <FinalTinyMCETextEditor
              name="source"
              loading={loading}
              value={currentInput}
              parse={v => v}
              config={{images: true, imageUploadURL, fullScreen: false}}
              height="70vh"
            />
          )}
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
  modalTitle: PropTypes.string.isRequired,
};

NoteEditor.defaultProps = {
  getNoteURL: null,
};
