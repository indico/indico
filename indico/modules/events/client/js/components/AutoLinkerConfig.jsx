// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import autoLinkerConfigURL from 'indico-url:events.autolinker_config';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Button, Form, List, Message, Segment} from 'semantic-ui-react';

import {handleSubmissionError} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

import {rulePropTypes} from './propTypes';
import './AutoLinkerConfig.module.scss';

/**
 * A simple rule-adding form
 */
function RuleEditor({regex, url, onChange}) {
  function _onChange(key, value) {
    const data = {regex, url};
    data[key] = value;
    onChange(data);
  }

  return (
    <>
      <Form.Input
        fluid
        placeholder={Translate.string('Regex Pattern')}
        value={regex}
        onChange={(__, {value}) => _onChange('regex', value)}
      />
      <Form.Input
        fluid
        placeholder={Translate.string('URL with placeholder(s)')}
        value={url}
        onChange={(__, {value}) => _onChange('url', value)}
      />
    </>
  );
}

RuleEditor.propTypes = {
  regex: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};

/**
 * The Auto-linker config panel
 */
export default function AutoLinkerConfig({rules, onChange}) {
  const [newRule, setNewRule] = useState({regex: '', url: ''});
  const [error, setError] = useState(null);

  const onAdd = async () => {
    try {
      const newRules = [...rules, newRule];
      await indicoAxios.post(autoLinkerConfigURL(), {rules: newRules});
      onChange(newRules);
      setNewRule({regex: '', url: ''});
    } catch (e) {
      if (e?.response?.data?.error?.message) {
        setError(e.response.data.error.message);
      } else {
        // more general error
        setError(handleSubmissionError(e).rules);
      }
    }
  };

  const onRemove = async n => {
    try {
      const newRules = [...rules];
      const [oldRule] = newRules.splice(n, 1);
      await indicoAxios.post(autoLinkerConfigURL(), {rules: newRules});
      onChange(newRules);
      setNewRule(oldRule);
    } catch (e) {
      handleAxiosError(e);
    }
  };

  return (
    <>
      {error ? <Message error>{error}</Message> : null}
      <Segment styleName="list-segment">
        <List divided relaxed>
          {rules.map(({regex, url}, n) => {
            const encodedURI = encodeURIComponent(url.replace(/\{(\d+)\}/g, '\\$1'));
            const encodedRegex = encodeURIComponent(regex.replace(/"/g, '\\"'));

            return (
              <List.Item key={regex}>
                <List.Content floated="right">
                  <Button
                    basic
                    icon="share"
                    as="a"
                    target="_blank"
                    title={Translate.string('Analyze on regex101.com')}
                    href={`https://regex101.com/?flavor=python&regex=${encodedRegex}&subst=${encodedURI}&flags=g`}
                    rel="noreferrer"
                  />
                  <Button
                    icon="trash alternate outline"
                    color="red"
                    title={Translate.string('Delete entry')}
                    onClick={() => {
                      setError(null);
                      onRemove(n);
                    }}
                  />
                </List.Content>
                <List.Content>
                  <List.Header>{regex}</List.Header>
                  {url}
                </List.Content>
              </List.Item>
            );
          })}
        </List>
        <Form>
          <Form.Group widths="equal" styleName="rule-editor-row">
            <RuleEditor {...newRule} onChange={setNewRule} />
            <Button
              icon="plus"
              title={Translate.string('Add entry')}
              onClick={() => {
                setError(null);
                onAdd();
              }}
              primary
            />
          </Form.Group>
        </Form>
      </Segment>
    </>
  );
}

AutoLinkerConfig.propTypes = {
  rules: PropTypes.arrayOf(PropTypes.shape(rulePropTypes)).isRequired,
  onChange: PropTypes.func.isRequired,
};
