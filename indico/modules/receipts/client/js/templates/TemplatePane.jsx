// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import templateListURL from 'indico-url:receipts.template_list';

import Editor from '@monaco-editor/react';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useEffect, useRef, useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Link} from 'react-router-dom';
import {Button, Form, Message} from 'semantic-ui-react';

import {ManagementPageSubTitle} from 'indico/react/components';
import {FinalField, FinalInput, FinalSubmitButton, parsers} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import Nexus from 'indico/react/util/Nexus';

import {targetLocatorSchema, templateSchema} from './util';
import './TemplatePane.module.scss';

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

export default function TemplatePane({template, onSubmit, targetLocator, editorHeight}) {
  const [currentFileExt, setFileExt] = useState('html');
  const codeValues = _.pick(template, ['html', 'css', 'yaml']);

  const editorRef = useRef(null);

  useEffect(() => {
    editorRef.current?.focus();
  }, [currentFileExt]);

  return (
    <>
      <ManagementPageSubTitle title={Translate.string('Add Receipt / Certificate template')} />
      <FinalForm
        onSubmit={onSubmit}
        initialValues={{title: template?.title || null, ...codeValues}}
        initialValuesEqual={_.isEqual}
      >
        {({handleSubmit}) => (
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
                      <Editor
                        height={`${editorHeight}px`}
                        theme="vs-dark"
                        path={FILES[fileExt].fileName}
                        defaultLanguage={FILES[fileExt].syntax}
                        value={input.value}
                        onChange={input.onChange}
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
    </>
  );
}

TemplatePane.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  template: templateSchema,
  targetLocator: targetLocatorSchema.isRequired,
  editorHeight: PropTypes.number,
};

TemplatePane.defaultProps = {
  template: {},
  editorHeight: 800,
};
