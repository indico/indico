// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import autoLinkerConfigUrl from 'indico-url:events.autolinker_config';
import autoLinkerRulesUrl from 'indico-url:events.autolinker_rules';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Button, Form, List, Loader, Message, Segment} from 'semantic-ui-react';

import {handleSubmissionError} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

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
export default function AutoLinkerConfig() {
  const {data, loading: isLoadingRules, reFetch} = useIndicoAxios(autoLinkerRulesUrl(), {
    camelize: true,
  });

  const [newRule, setNewRule] = useState({regex: '', url: ''});
  const [error, setError] = useState(null);

  const onAdd = async () => {
    try {
      const newRules = [...data.rules, newRule];
      await indicoAxios.post(autoLinkerConfigUrl(), {rules: newRules});
      reFetch();
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
      const newRules = [...data.rules];
      newRules.splice(n, 1);
      await indicoAxios.post(autoLinkerConfigUrl(), {rules: newRules});
      reFetch();
      setNewRule({regex: '', url: ''});
    } catch (e) {
      handleAxiosError(e);
    }
  };

  return isLoadingRules ? (
    <Loader />
  ) : (
    <>
      {error ? <Message error>{error}</Message> : null}
      <Segment styleName="list-segment">
        <List divided relaxed>
          {data.rules.map(({regex, url}, n) => (
            <List.Item key={regex}>
              <List.Content floated="right">
                <Button
                  icon="trash alternate outline"
                  color="red"
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
          ))}
        </List>
        <Form>
          <Form.Group widths="equal">
            <RuleEditor {...newRule} onChange={setNewRule} />
            <Button
              icon="plus"
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
