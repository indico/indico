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
import {Popup} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import {Link, Route} from 'react-router-dom';

import {Translate} from 'indico/react/i18n';

import './MenuItem.module.scss';


export default function MenuItem({path, children, disabled, onClick}) {
    if (disabled) {
        return (
            <Route path={path}>
                <Popup trigger={<li styleName="rb-menu-item"><span styleName="disabled">{children}</span></li>}
                       content={Translate.string('Coming soon!')}
                       position="bottom center" />
            </Route>
        );
    }
    return (
        <Route path={path}>
            {({match}) => (
                <li className={match ? 'selected' : ''}
                    styleName="rb-menu-item">
                    <Link to={path} replace={!!match} onClick={onClick}>
                        {children}
                    </Link>
                </li>
            )}
        </Route>
    );
}

MenuItem.propTypes = {
    path: PropTypes.string.isRequired,
    children: PropTypes.node.isRequired,
    disabled: PropTypes.bool,
    onClick: PropTypes.func.isRequired,
};

MenuItem.defaultProps = {
    disabled: false,
};
