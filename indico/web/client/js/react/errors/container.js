// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {connect} from 'react-redux';

import ErrorDialog from './component';
import {clearError, showReportForm} from './actions';

const mapStateToProps = ({errors: {errorList, formVisible}}) => ({
  errorData: errorList[0],
  remainingErrors: errorList.length ? errorList.length - 1 : 0,
  formVisible,
  dialogVisible: !!errorList.length,
});

const mapDispatchToProps = dispatch => ({
  showReportForm() {
    dispatch(showReportForm());
  },
  clearError() {
    dispatch(clearError());
  },
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(ErrorDialog);
