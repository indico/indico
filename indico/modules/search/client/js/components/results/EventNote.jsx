// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {List} from 'semantic-ui-react';

import {Path, pathPropType} from './Path';

import '../ResultList.module.scss';

const EventNote = ({title, url, content, highlight, categoryPath, eventPath}) => (
  <div styleName="item">
    <List.Header styleName="header">
      <a href={url}>{title}</a>
    </List.Header>
    <List.Description styleName="description">
      {highlight?.content
        ?.slice(0, 3) // eslint-disable-next-line react/no-array-index-key
        .map((html, idx) => <span key={html + idx} dangerouslySetInnerHTML={{__html: html}} />) || (
        <span>{content.slice(0, 240)}</span>
      )}
      {categoryPath.length !== 0 && (
        <List.Item>
          <List.Description>
            <Path path={[...categoryPath, ...eventPath]} />
          </List.Description>
        </List.Item>
      )}
    </List.Description>
  </div>
);

EventNote.propTypes = {
  title: PropTypes.string.isRequired,
  content: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  highlight: PropTypes.shape({
    content: PropTypes.array,
  }),
  categoryPath: pathPropType.isRequired,
  eventPath: pathPropType.isRequired,
};

EventNote.defaultProps = {
  highlight: {},
};

export default EventNote;
