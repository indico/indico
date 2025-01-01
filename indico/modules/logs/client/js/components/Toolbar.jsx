// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';

import Filter from '../containers/Filter';
import SearchBox from '../containers/SearchBox';

class Toolbar extends React.Component {
  static propTypes = {
    realms: PropTypes.object.isRequired,
  };

  render() {
    const {realms} = this.props;
    return (
      <div className="toolbars">
        <Filter realms={realms} />
        <SearchBox />
      </div>
    );
  }
}

const mapStateToProps = ({staticData}) => ({
  realms: staticData.realms,
});

export default connect(mapStateToProps)(Toolbar);
