// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import debounce from 'lodash/debounce';
import {connect} from 'react-redux';

import {setKeyword, fetchLogEntries, setPage} from '../actions';
import SearchBox from '../components/SearchBox';

const mapDispatchToProps = dispatch => ({
  setKeyword: debounce(keyword => {
    dispatch(setKeyword(keyword));
    dispatch(setPage(1));
    dispatch(fetchLogEntries());
  }, 250),
});

export default connect(
  null,
  mapDispatchToProps
)(SearchBox);
