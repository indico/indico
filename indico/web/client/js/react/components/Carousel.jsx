// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {Translate} from 'indico/react/i18n';

import './Carousel.module.scss';

/**
 * Named buttons that select a pane.
 */
function PaneSwitcher({panes, onClick, activePane}) {
  return (
    <ul styleName="pane-switcher">
      {panes.map(({key, label}, n) => (
        <li key={key}>
          <button
            type="button"
            className={activePane === n ? 'active' : ''}
            styleName="pane-switcher-item"
            onClick={() => onClick(n)}
          >
            <span styleName="pane-switcher-label">
              {activePane === n && <>{Translate.string('Current pane')}: </>}
              {label}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}

PaneSwitcher.propTypes = {
  panes: PropTypes.arrayOf(
    PropTypes.shape({key: PropTypes.string.isRequired, label: PropTypes.string.isRequired})
  ).isRequired,
  /** onClick handler (pane index passed as parameter) */
  onClick: PropTypes.func.isRequired,
  /** the currently active pane */
  activePane: PropTypes.number.isRequired,
};

/**
 * A manually controlled widget that shows one pane at a time.
 */
export default class Carousel extends React.PureComponent {
  static propTypes = {
    /** an array of named panes */
    panes: PropTypes.arrayOf(
      PropTypes.shape({
        key: PropTypes.string.isRequired,
        label: PropTypes.string.isRequired,
        content: PropTypes.node.isRequired,
      })
    ).isRequired,
  };

  state = {
    activePane: 0,
  };

  selectPane = activePane => {
    this.setState({activePane});
  };

  render() {
    const {panes} = this.props;
    const {activePane} = this.state;
    return (
      <div styleName="carousel">
        <div styleName="pane-container">
          {panes.map(({key, content}, n) => (
            <div key={key} styleName="carousel-page" hidden={n !== activePane}>
              {content}
            </div>
          ))}
        </div>
        <PaneSwitcher activePane={activePane} panes={panes} onClick={this.selectPane} />
      </div>
    );
  }
}
