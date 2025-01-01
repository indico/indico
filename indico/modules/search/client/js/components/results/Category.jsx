// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {List} from 'semantic-ui-react';

import {Path, pathPropType} from './Path';

import '../ResultList.module.scss';

export default function Category({title, categoryPath, url}) {
  return (
    <div styleName="item">
      <List.Header styleName="header">
        <a href={url}>{title}</a>
      </List.Header>
      {categoryPath.length !== 0 && (
        <div styleName="description">
          <List.Description>
            <Path path={categoryPath} />
          </List.Description>
        </div>
      )}
    </div>
  );
}

Category.propTypes = {
  title: PropTypes.string.isRequired,
  categoryPath: pathPropType.isRequired,
  url: PropTypes.string.isRequired,
};
