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

export const ADD_ERROR = 'ADD_ERROR';
export const CLEAR_ERROR = 'CLEAR_ERROR';
export const SHOW_REPORT_FORM = 'SHOW_REPORT_FORM';


export function addError(error) {
    return {
        type: ADD_ERROR,
        error: {
            title: error.title,
            message: error.message,
            errorUUID: error.error_uuid,
            reportable: !!error.error_uuid,
        }
    };
}


export function clearError() {
    return {type: CLEAR_ERROR};
}


export function showReportForm() {
    return {type: SHOW_REPORT_FORM};
}
