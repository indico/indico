// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Form, Grid, Icon, Segment} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {AutoLinkerPlugin, Markdown} from 'indico/react/util';

import {rulePropTypes} from './propTypes';

/**
 * A "test drive" widget which just takes Markdown and renders it using the auto-linker rules which are provided
 */
export default function AutoLinkerTestDrive({rules}) {
  const [source, setSource] = useState('');

  const onChange = value => {
    setSource(value);
  };

  return (
    <Segment>
      <h2>
        <Icon name="car" />
        <Translate>Test drive</Translate>
      </h2>
      <p>
        <Translate>
          You can write some markdown below and see how the above rules are applied
        </Translate>
      </p>
      <Form>
        <Grid columns={2}>
          <Grid.Column>
            <Form.TextArea
              placeholder={Translate.string('Write some Markdown here...')}
              value={source}
              onChange={(__, {value}) => onChange(value)}
            />
          </Grid.Column>
          <Grid.Column>
            {source ? (
              <Segment>
                <Markdown targetBlank remarkPlugins={[[AutoLinkerPlugin, {rules}]]}>
                  {source}
                </Markdown>
              </Segment>
            ) : null}
          </Grid.Column>
        </Grid>
      </Form>
    </Segment>
  );
}

AutoLinkerTestDrive.propTypes = {
  rules: PropTypes.arrayOf(PropTypes.shape(rulePropTypes)).isRequired,
};
