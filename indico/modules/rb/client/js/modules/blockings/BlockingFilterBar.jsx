// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {Button, Dropdown} from 'semantic-ui-react';

import {ResponsivePopup} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {toClasses} from 'indico/react/util';

import * as blockingsActions from './actions';
import * as blockingsSelectors from './selectors';

const timeframeOptions = {
  recent: Translate.string('Active and future'),
  year: Translate.string('All blockings this year'),
  all: Translate.string('All blockings'),
};

class BlockingFilterBar extends React.Component {
  static propTypes = {
    filters: PropTypes.shape({
      myBlockings: PropTypes.bool.isRequired,
      myRooms: PropTypes.bool.isRequired,
      timeframe: PropTypes.oneOf(['recent', 'year', 'all']),
    }).isRequired,
    actions: PropTypes.exact({
      setFilterParameter: PropTypes.func.isRequired,
    }).isRequired,
  };

  render() {
    const {
      filters: {myBlockings, myRooms, timeframe},
      actions: {setFilterParameter},
    } = this.props;
    const filterByDateOptions = Object.entries(timeframeOptions).map(([key, value]) => ({
      text: value,
      value: key,
    }));

    return (
      <div className="filter-row">
        <div className="filter-row-filters">
          <Dropdown
            text={timeframe ? timeframeOptions[timeframe] : Translate.string('Filter by date')}
            className={toClasses({primary: !!timeframe})}
            options={filterByDateOptions}
            direction="right"
            value={timeframe}
            onChange={(__, {value}) => setFilterParameter('timeframe', value)}
            button
            floating
          />
          <Button.Group>
            <ResponsivePopup
              trigger={
                <Button
                  content={Translate.string('Blockings in my rooms')}
                  primary={myRooms}
                  onClick={() => setFilterParameter('myRooms', !myRooms)}
                />
              }
              content={Translate.string('Show only blockings in my rooms')}
            />
            <ResponsivePopup
              trigger={
                <Button
                  content={Translate.string('My blockings')}
                  primary={myBlockings}
                  onClick={() => setFilterParameter('myBlockings', !myBlockings)}
                />
              }
              content={Translate.string('Show only my blockings')}
            />
          </Button.Group>
        </div>
      </div>
    );
  }
}

export default connect(
  state => ({
    filters: blockingsSelectors.getFilters(state),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        setFilterParameter: blockingsActions.setFilterParameter,
      },
      dispatch
    ),
  })
)(BlockingFilterBar);
