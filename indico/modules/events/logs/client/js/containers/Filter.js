// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {connect} from 'react-redux';
import Filter from '../components/Filter';
import {setFilter, fetchLogEntries, setPage} from '../actions';

const mapStateToProps = ({logs}) => ({
  filters: logs.filters,
});

const mapDispatchToProps = dispatch => ({
  setFilter: filter => {
    dispatch(setFilter(filter));
    dispatch(setPage(1));
    dispatch(fetchLogEntries());
  },
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Filter);
