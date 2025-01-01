// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import templateListURL from 'indico-url:receipts.template_list';

import MonacoEditor, {loader} from '@monaco-editor/react';
import _ from 'lodash';
// weird import needed because of https://github.com/microsoft/monaco-editor/issues/2874
import * as monacoEditor from 'monaco-editor/esm/vs/editor/editor.api';
import PropTypes from 'prop-types';
import React, {useEffect, useRef, useState} from 'react';
import {Form as FinalForm, FormSpy} from 'react-final-form';
import {Link} from 'react-router-dom';
import {Button, Dimmer, Form, Loader, Message, Segment} from 'semantic-ui-react';

import {
  FinalField,
  FinalInput,
  FinalSubmitButton,
  FinalUnloadPrompt,
  formatters,
} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import Nexus from 'indico/react/util/Nexus';

import {targetLocatorSchema, templateSchema} from './util';

import './Editor.module.scss';

// load monaco editor locally instead of from a CDN
loader.config({monaco: monacoEditor});

// Note: if you ever end up adding more file types, or refactoring this into something more
// generic to use the editor elsewhere, you also need to update the webpack config since it
// is configured to only include a subset of languages (search for `MonacoEditorWebpackPlugin`)
const FILES = {
  html: {
    syntax: 'html',
    fileName: 'template.html',
  },
  css: {
    syntax: 'css',
    fileName: 'theme.css',
  },
  yaml: {
    syntax: 'yaml',
    fileName: 'metadata.yaml',
  },
};

export default function Editor({
  template,
  onChange,
  onSubmit,
  editorHeight,
  targetLocator,
  loading,
  add,
}) {
  const [currentFileExt, setFileExt] = useState('html');
  const codeValues = _.pick(template, ['html', 'css', 'yaml']);
  const editorRef = useRef(null);

  useEffect(() => {
    editorRef.current?.focus();
  }, [currentFileExt]);

  return (
    <FinalForm
      onSubmit={onSubmit}
      initialValues={{
        title: template?.title || null,
        default_filename: template?.default_filename || '',
        ...codeValues,
      }}
      initialValuesEqual={_.isEqual}
    >
      {({handleSubmit, values}) => (
        <Form onSubmit={handleSubmit} subscription={{dirty: true}}>
          <FormSpy subscription={{dirtyFieldsSinceLastSubmit: true}}>
            {/*
               The form stays dirty when we submit for creation so we need to disable the unload
               prompt if there were no chances since submitting it. For editing we just use the
               standard behavior since the dirty flag is properly cleared.
            */}
            {({dirtyFieldsSinceLastSubmit}) =>
              (!!template.owner || Object.values(dirtyFieldsSinceLastSubmit).some(x => x)) && (
                <FinalUnloadPrompt router />
              )
            }
          </FormSpy>
          <Form.Group widths="equal">
            <FinalInput
              name="title"
              label={Translate.string('Title')}
              type="text"
              disabled={loading}
              required
              rows={24}
            />
            <FinalInput
              name="default_filename"
              label={Translate.string('Default filename')}
              type="text"
              componentLabel="-{n}.pdf"
              labelPosition="right"
              format={formatters.slugify}
              disabled={loading}
              formatOnBlur
            />
          </Form.Group>
          <Button.Group attached="top">
            {['html', 'css', 'yaml'].map(format => (
              <Button
                type="button"
                primary={format === currentFileExt}
                key={format}
                onClick={() => setFileExt(format)}
              >
                {FILES[format].fileName}
              </Button>
            ))}
          </Button.Group>
          {['html', 'css', 'yaml'].map(fileExt => (
            <FinalField
              key={fileExt}
              name={fileExt}
              initialValue={template[fileExt]}
              parse={v => v}
            >
              {({input, meta}) => (
                <>
                  <Nexus
                    target={<div style={{height: `${editorHeight}px`, width: '100%'}} />}
                    open={fileExt === currentFileExt}
                  >
                    {loading ? (
                      <Segment style={{height: `${editorHeight}px`}} styleName="loading-segment">
                        <Dimmer active>
                          <Loader />
                        </Dimmer>
                      </Segment>
                    ) : (
                      <MonacoEditor
                        height={`${editorHeight}px`}
                        theme="vs-dark"
                        path={FILES[fileExt].fileName}
                        defaultLanguage={FILES[fileExt].syntax}
                        value={input.value}
                        onChange={value => {
                          onChange({...values, [fileExt]: value});
                          input.onChange(value);
                        }}
                        onMount={(editor, monaco) => {
                          editorRef.current = editor;
                          editor.addCommand(
                            // eslint-disable-next-line no-bitwise
                            monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS,
                            handleSubmit
                          );
                        }}
                        options={{minimap: {enabled: false}}}
                      />
                    )}
                  </Nexus>
                  <Message error visible={!!meta.submitError}>
                    {meta.submitError}
                  </Message>
                </>
              )}
            </FinalField>
          ))}
          <Form.Group styleName="buttons">
            <FinalSubmitButton label={Translate.string('Save')} disabledUntilChange={!add} />
            <Link to={templateListURL(targetLocator)} className="ui button">
              <Translate>Cancel</Translate>
            </Link>
          </Form.Group>
        </Form>
      )}
    </FinalForm>
  );
}

Editor.propTypes = {
  template: templateSchema.isRequired,
  onChange: PropTypes.func.isRequired,
  onSubmit: PropTypes.func.isRequired,
  editorHeight: PropTypes.number.isRequired,
  targetLocator: targetLocatorSchema.isRequired,
  loading: PropTypes.bool,
  add: PropTypes.bool,
};

Editor.defaultProps = {
  loading: false,
  add: false,
};
