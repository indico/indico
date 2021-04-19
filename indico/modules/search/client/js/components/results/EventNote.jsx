// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {List} from 'semantic-ui-react';
import '../ResultList.module.scss';

const EventNote = ({title, url, content, highlight}) => (
  <div styleName="item">
    <List.Header styleName="header">
      <a href={url}>{title}</a>
    </List.Header>
    <List.Description styleName="description">
      {highlight?.content
        .slice(0, 3) // eslint-disable-next-line react/no-array-index-key
        .map((html, idx) => <span key={html + idx} dangerouslySetInnerHTML={{__html: html}} />) || (
        <span>{content.slice(0, 240)}</span>
      )}
    </List.Description>
  </div>
);

EventNote.propTypes = {
  title: PropTypes.string.isRequired,
  content: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  highlight: PropTypes.shape({
    content: PropTypes.array.isRequired,
  }),
};

EventNote.defaultProps = {
  highlight: {},
};

export default EventNote;
