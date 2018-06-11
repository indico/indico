/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

import {connect} from 'react-redux';
import {reduxForm, reset} from 'redux-form';

import ErrorDialog from './component';
import {clearError, showReportForm} from './actions';


const mapStateToProps = ({errors: {errorList, formVisible}}) => ({
    errorData: errorList[0],
    remainingErrors: errorList.length ? errorList.length - 1 : 0,
    formVisible,
    dialogVisible: !!errorList.length,
});

const mapDispatchToProps = (dispatch) => ({
    showReportForm() {
        dispatch(showReportForm());
    },
    clearError() {
        dispatch(clearError());
        dispatch(reset('reportError'));
    },
});

const container = connect(mapStateToProps, mapDispatchToProps)(ErrorDialog);
export default reduxForm({
    form: 'reportError',
    touchOnBlur: false,
    propNamespace: 'form',
})(container);
