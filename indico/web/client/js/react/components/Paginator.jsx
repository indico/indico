// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import IButton from './IButton';

import './style/paginator.scss';

export default class Paginator extends React.Component {
  static propTypes = {
    currentPage: PropTypes.number.isRequired,
    pages: PropTypes.array.isRequired,
    changePage: PropTypes.func.isRequired,
    hideIfSinglePage: PropTypes.bool,
  };

  static defaultProps = {
    hideIfSinglePage: true,
  };

  render() {
    const {pages, currentPage, changePage, hideIfSinglePage} = this.props;

    if (pages.length < 2 && hideIfSinglePage) {
      return null;
    }

    let ellipsisKey = 0;
    function getPageKey(number) {
      return number === null ? `ellipsis-${++ellipsisKey}` : `page-${number}`;
    }

    return (
      <ul className="paginator">
        {pages.length > 1 && currentPage !== 1 && (
          <li key="prev-page" className="page-arrow">
            <IButton icon="prev" onClick={() => changePage(currentPage - 1)} />
          </li>
        )}
        {pages.map(number => (
          <li key={getPageKey(number)} className="page-number">
            {number === null ? (
              <span className="superfluous-text">…</span>
            ) : (
              <IButton highlight={number === currentPage} onClick={() => changePage(number)}>
                {number}
              </IButton>
            )}
          </li>
        ))}
        {pages.length > 1 && currentPage !== pages[pages.length - 1] && (
          <li key="next-page" className="page-arrow">
            <IButton icon="next" onClick={() => changePage(currentPage + 1)} />
          </li>
        )}
      </ul>
    );
  }
}
