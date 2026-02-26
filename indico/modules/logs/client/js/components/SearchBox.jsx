// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

export default class SearchBox extends React.Component {
  static propTypes = {
    keyword: PropTypes.string,
    setKeyword: PropTypes.func.isRequired,
  };

  static defaultProps = {
    keyword: '',
  };

  render() {
    const {keyword, setKeyword} = this.props;
    return (
      <div className="toolbar">
        <div className="group">
          <span className="i-button label">
            <span className="icon-search" />
          </span>
          <input
            type="text"
            value={keyword || ''}
            onChange={e => setKeyword(e.target.value.trim())}
          />
        </div>
      </div>
    );
  }
}
