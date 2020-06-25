// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {connect} from 'react-redux';

import LogEntryModal from '../components/LogEntryModal';
import {
  fetchLogEntries,
  setDetailedView,
  setMetadataQuery,
  setPage,
  viewNextEntry,
  viewPrevEntry,
} from '../actions';

const mapStateToProps = ({logs}) => ({
  currentViewIndex: logs.currentViewIndex,
  currentPage: logs.currentPage,
  totalPageCount: logs.totalPageCount,
});

const mapDispatchToProps = dispatch => ({
  setDetailedView: entryIndex => {
    dispatch(setDetailedView(entryIndex));
  },
  prevEntry: () => {
    dispatch(viewPrevEntry());
  },
  nextEntry: () => {
    dispatch(viewNextEntry());
  },
  relatedEntries: async metadataQuery => {
    dispatch(setMetadataQuery(metadataQuery));
    await dispatch(fetchLogEntries());
    dispatch(setDetailedView(null));
    dispatch(setPage(1));
  },
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(LogEntryModal);
