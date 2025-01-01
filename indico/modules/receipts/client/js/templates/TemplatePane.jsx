// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import eventImagesURL from 'indico-url:receipts.images';
import templateLivePreviewURL from 'indico-url:receipts.template_live_preview';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {Grid, Header, Icon, Segment} from 'semantic-ui-react';

import {ManagementPageSubTitle} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

import Editor from './Editor';
import Previewer from './Previewer';
import {targetLocatorSchema, templateSchema} from './util';

export default function TemplatePane({
  template,
  onSubmit,
  targetLocator,
  editorHeight,
  add,
  loading,
}) {
  const [data, setData] = useState({});

  useEffect(() => {
    setData({
      title: template.title,
      ..._.pick(template, ['html', 'css', 'yaml']),
    });
  }, [template]);

  return (
    <>
      <ManagementPageSubTitle
        title={
          add
            ? Translate.string('Add document template')
            : Translate.string('Edit document template')
        }
      />
      <Grid columns={2} divided>
        <Grid.Row>
          <Grid.Column>
            <Editor
              onSubmit={onSubmit}
              template={template}
              editorHeight={editorHeight}
              targetLocator={targetLocator}
              onChange={setData}
              loading={loading}
              add={add}
            />
          </Grid.Column>
          <Grid.Column>
            {data.html && data.html.length >= 3 ? (
              <Previewer
                url={templateLivePreviewURL(targetLocator)}
                data={data}
                fetchImagesURL={'event_id' in targetLocator ? eventImagesURL(targetLocator) : null}
              />
            ) : (
              <Segment placeholder>
                <Header icon>
                  <Icon name="eye" />
                  <Translate>Start writing a template to see the preview here...</Translate>
                </Header>
              </Segment>
            )}
          </Grid.Column>
        </Grid.Row>
      </Grid>
    </>
  );
}

TemplatePane.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  template: templateSchema,
  targetLocator: targetLocatorSchema.isRequired,
  editorHeight: PropTypes.number,
  add: PropTypes.bool,
  loading: PropTypes.bool,
};

TemplatePane.defaultProps = {
  template: {html: '', css: '', yaml: ''},
  editorHeight: 800,
  add: false,
  loading: false,
};
