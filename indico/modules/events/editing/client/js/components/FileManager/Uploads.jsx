// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import {Icon, Progress, Segment} from 'semantic-ui-react';

import './FileManager.module.scss';

export default function Uploads({uploads}) {
  const uploadList = _.sortBy(Object.entries(uploads), x => x[0]);
  return (
    <div styleName="uploading-file-list">
      {uploadList.map(([key, {file: {name}, percent}]) => (
        <Segment key={key} styleName="uploading-file-row">
          <Icon loading name="spinner" />
          <span styleName="file-state" className="uploading">
            {name}
          </span>
          <Progress percent={percent} attached="bottom" color="blue" />
        </Segment>
      ))}
    </div>
  );
}

Uploads.propTypes = {
  uploads: PropTypes.objectOf(
    PropTypes.shape({
      file: PropTypes.shape({
        name: PropTypes.string.isRequired,
      }).isRequired,
      percent: PropTypes.number,
    })
  ).isRequired,
};
