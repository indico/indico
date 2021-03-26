// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {List} from 'semantic-ui-react';
import '../ResultList.module.scss';

const EventNote = ({title, url, content, highlight}) => {
  return (
    <div styleName="item">
      <List.Header styleName="header">
        <a href={url}>{title}</a>
      </List.Header>
      <List.Description styleName="description">
        {highlight.content ? (
          highlight.content
            .slice(0, 3)
            .map(html => <span key={html} dangerouslySetInnerHTML={{__html: html}} />)
        ) : (
          <span>{content.slice(0, 240)}</span>
        )}
      </List.Description>
    </div>
  );
};

EventNote.propTypes = {
  title: PropTypes.string.isRequired,
  content: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  highlight: PropTypes.array,
};

EventNote.defaultProps = {
  highlight: [],
};

export default EventNote;
