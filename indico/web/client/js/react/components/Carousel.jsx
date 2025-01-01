// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';

import './Carousel.module.scss';

/**
 * A purely CSS animation-based Progress Indicator
 */
class ProgressIndicator extends React.PureComponent {
  static propTypes = {
    /** duration of the animation (ms) */
    duration: PropTypes.number.isRequired,
    /** whether the widget is disabled */
    disabled: PropTypes.bool,
  };

  static defaultProps = {
    disabled: false,
  };

  constructor(props) {
    super(props);
    this.divRef = React.createRef();
    this.frame = null;
  }

  componentDidMount() {
    const {duration} = this.props;

    /* The purpose of these "beautiful" next 8 or so lines
     * is forcing a rendering of the element in its initial
     * state (width: 0), then set the transition properties
     * and finally force another rendering at width: 100%.
     * This will trigger the CSS animation.
     * I've written worse things in my career.
     */
    this.frame = requestAnimationFrame(() => {
      this.divRef.current.style.width = 0;
      this.divRef.current.style.transition = `width ${duration}ms linear`;

      this.frame = requestAnimationFrame(() => {
        this.divRef.current.style.width = '100%';
        this.frame = null;
      });
    });
  }

  componentWillUnmount() {
    this.divRef.current.style.transition = null;
    if (this.frame !== null) {
      cancelAnimationFrame(this.frame);
      this.frame = null;
    }
  }

  render() {
    const {disabled} = this.props;
    return (
      <div styleName="progress-indicator" className={disabled ? 'disabled' : ''}>
        <div styleName="progress-bar" ref={this.divRef} />
      </div>
    );
  }
}

/**
 * The little dots that can be used to switch panes.
 */
function PaneSwitcher({numPanes, onClick, activePane}) {
  return (
    <ul styleName="pane-switcher">
      {_.times(numPanes, n => (
        <li
          key={n}
          className={activePane === n ? 'active' : ''}
          styleName="pane-switcher-item"
          onClick={() => onClick(n)}
        />
      ))}
    </ul>
  );
}

PaneSwitcher.propTypes = {
  /** The number of "dots" to show */
  numPanes: PropTypes.number.isRequired,
  /** onClick handler (pane index passed as parameter) */
  onClick: PropTypes.func.isRequired,
  /** the currently active pane */
  activePane: PropTypes.number.isRequired,
};

/**
 * A purely CSS-based carousel widget, which switches between a given number of panes.
 */
export default class Carousel extends React.PureComponent {
  static propTypes = {
    /** an array of {key, content, delay?} objects which will define each pane */
    panes: PropTypes.arrayOf(
      PropTypes.shape({
        key: PropTypes.string.isRequired,
        content: PropTypes.node.isRequired,
        delay: PropTypes.number,
      })
    ).isRequired,
    /** the delay to wait at each pane, by default */
    delay: PropTypes.number,
  };

  static defaultProps = {
    delay: 10,
  };

  state = {
    /** id of the active pane */
    activePane: 0,
    /** this will be set to 'true' if the user has taken control */
    userOverridden: false,
  };

  componentDidMount() {
    const {
      delay: globalDelay,
      panes: [{delay: paneDelay}],
    } = this.props;
    this.timeout = setTimeout(this.switchPane, (paneDelay || globalDelay) * 1000);
  }

  componentWillUnmount() {
    if (this.timeout) {
      // cancel timeout for next transition
      clearTimeout(this.timeout);
    }
  }

  get numPanes() {
    const {panes} = this.props;
    return panes.length;
  }

  switchPane = () => {
    let {activePane} = this.state;
    activePane = (activePane + 1) % this.numPanes;
    const {panes, delay: globalDelay} = this.props;
    const {delay: paneDelay} = panes[activePane];

    this.setState({
      activePane,
    });

    // Schedule next switch
    this.timeout = setTimeout(this.switchPane, (paneDelay || globalDelay) * 1000);
  };

  forcePaneSwitch = newPane => {
    // cancel automatic switching (forever!)
    clearTimeout(this.timeout);
    this.timeout = null;

    this.setState({
      activePane: newPane,
      userOverridden: true,
    });
  };

  render() {
    const {panes, delay: globalDelay} = this.props;
    const {activePane, userOverridden} = this.state;
    const {delay: paneDelay} = panes[activePane];
    return (
      <div styleName="carousel">
        <div styleName="pane-container">
          {panes.map(({key, content}, n) => (
            <div
              key={key}
              styleName="carousel-page"
              style={{marginLeft: n === 0 ? `-${activePane * 100}%` : null}}
            >
              {content}
            </div>
          ))}
        </div>
        <PaneSwitcher
          activePane={activePane}
          numPanes={panes.length}
          onClick={this.forcePaneSwitch}
        />
        <ProgressIndicator
          disabled={userOverridden}
          key={activePane}
          duration={(paneDelay || globalDelay) * 1000}
        />
      </div>
    );
  }
}
