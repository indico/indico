// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import templateListURL from 'indico-url:receipts.template_list';

import MonacoEditor from '@monaco-editor/react';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useEffect, useRef, useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Link} from 'react-router-dom';
import {Button, Form, Message} from 'semantic-ui-react';

import {FinalField, FinalInput, FinalSubmitButton, parsers} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import Nexus from 'indico/react/util/Nexus';

import './TemplatePane.module.scss';
import {targetLocatorSchema, templateSchema} from './util';

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

export default function Editor({template, onChange, onSubmit, editorHeight, targetLocator}) {
  const [currentFileExt, setFileExt] = useState('html');
  const codeValues = _.pick(template, ['html', 'css', 'yaml']);

  const editorRef = useRef(null);

  useEffect(() => {
    editorRef.current?.focus();
  }, [currentFileExt]);

  return (
    <FinalForm
      onSubmit={onSubmit}
      initialValues={{title: template?.title || null, ...codeValues}}
      initialValuesEqual={_.isEqual}
    >
      {({handleSubmit, values}) => (
        <Form onSubmit={handleSubmit} subscription={{dirty: true}}>
          <FinalInput
            name="title"
            label="Title"
            component={Form.Input}
            type="text"
            required
            rows={24}
          />
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
              parse={parsers.nullIfEmpty}
            >
              {({input, meta}) => (
                <>
                  <Nexus
                    target={<div style={{height: `${editorHeight}px`, width: '100%'}} />}
                    open={fileExt === currentFileExt}
                  >
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
                      onMount={editor => {
                        editorRef.current = editor;
                      }}
                      options={{minimap: {enabled: false}}}
                    />
                  </Nexus>
                  <Message error visible={!!meta.submitError}>
                    {meta.submitError}
                  </Message>
                </>
              )}
            </FinalField>
          ))}
          <Form.Group styleName="buttons">
            <FinalSubmitButton label={Translate.string('Submit')} />
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
};
