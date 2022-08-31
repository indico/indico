// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import dummyDataURL from 'indico-url:receipts.dummy_data';
import templateListURL from 'indico-url:receipts.template_list';

import MonacoEditor from '@monaco-editor/react';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useEffect, useRef, useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Link} from 'react-router-dom';
import {Button, Form, Message, Popup} from 'semantic-ui-react';

import {FinalField, FinalInput, FinalSubmitButton, parsers} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Param, Translate} from 'indico/react/i18n';
import Nexus from 'indico/react/util/Nexus';

import './Editor.module.scss';
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

function FieldMap({fields}) {
  return Object.entries(fields).map(([k, v]) => (
    <div key={k} styleName="var-entry">
      <span styleName="key">{k}</span>:{' '}
      {_.isObject(v) ? (
        <div styleName="nested-value" style={{marginLeft: '1em'}}>
          <FieldMap fields={v} />
        </div>
      ) : (
        <span styleName="value">{JSON.stringify(v)}</span>
      )}
    </div>
  ));
}

FieldMap.propTypes = {
  fields: PropTypes.object,
};

function VariablesPopup({targetLocator, children}) {
  const {data} = useIndicoAxios({
    url: dummyDataURL(targetLocator),
  });

  return data ? (
    <Popup trigger={<a>{children}</a>} on="click">
      <Popup.Header>
        <Translate>Template Variables</Translate>
      </Popup.Header>
      <Popup.Content>
        <FieldMap fields={data} />
      </Popup.Content>
    </Popup>
  ) : null;
}

VariablesPopup.propTypes = {
  targetLocator: targetLocatorSchema.isRequired,
  children: PropTypes.node.isRequired,
};

export default function Editor({template, onChange, onSubmit, editorHeight, targetLocator}) {
  const [currentFileExt, setFileExt] = useState('html');
  const codeValues = _.pick(template, ['html', 'css', 'yaml']);

  const editorRef = useRef(null);

  useEffect(() => {
    editorRef.current?.focus();
  }, [currentFileExt]);

  const variablesLink = (
    <VariablesPopup targetLocator={{...targetLocator, template_id: template.id}} />
  );

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
          <Message color="orange" size="small">
            <Translate>
              You can use variables in your template. See the{' '}
              <Param name="link" wrapper={variablesLink}>
                full list here
              </Param>
              .
            </Translate>
          </Message>
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
