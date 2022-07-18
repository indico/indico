// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import templateLivePreviewURL from 'indico-url:receipts.template_live_preview';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Grid} from 'semantic-ui-react';

import {ManagementPageSubTitle} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

import Editor from './Editor';
import Previewer from './Previewer';
import {targetLocatorSchema, templateSchema} from './util';

export default function TemplatePane({template, onSubmit, targetLocator, editorHeight}) {
  const [data, setData] = useState({
    title: template.title,
    ..._.pick(template, ['html', 'css', 'yaml']),
  });
  const previewUrl = templateLivePreviewURL({template_id: template.id, ...targetLocator});
  return (
    <>
      <ManagementPageSubTitle title={Translate.string('Add Receipt / Certificate template')} />
      <Grid columns={2} divided>
        <Grid.Row>
          <Grid.Column>
            <Editor
              onSubmit={onSubmit}
              template={template}
              editorHeight={editorHeight}
              targetLocator={targetLocator}
              onChange={setData}
            />
          </Grid.Column>
          <Grid.Column>
            <Previewer url={previewUrl} data={data} />
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
};

TemplatePane.defaultProps = {
  template: {},
  editorHeight: 800,
};
