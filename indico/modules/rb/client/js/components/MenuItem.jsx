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

import React from 'react';
import {connect} from 'react-redux';
import PropTypes from 'prop-types';
import {Link, Route} from 'react-router-dom';
import * as globalActions from '../actions';

import './MenuItem.module.scss';


function MenuItem({namespace, path, children, resetPageState}) {
    return (
        <Route path={path}>
            {({match}) => (
                <li className={match ? 'selected' : ''} styleName="rb-menu-item">
                    <Link to={path} onClick={() => resetPageState(namespace)}>
                        {children}
                    </Link>
                </li>
            )}
        </Route>
    );
}

MenuItem.propTypes = {
    namespace: PropTypes.string.isRequired,
    path: PropTypes.string.isRequired,
    children: PropTypes.node.isRequired,
    resetPageState: PropTypes.func.isRequired,
};


export default connect(
    null,
    dispatch => ({
        resetPageState(namespace) {
            dispatch(globalActions.resetPageState(namespace));
        }
    })
)(MenuItem);
