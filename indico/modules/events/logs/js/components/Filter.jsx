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
import PropTypes from 'prop-types';

import IButton from 'indico/react/IButton';

export default class Filter extends React.Component {
    render() {
        const {realms, filters, setFilter} = this.props;
        return (
            <div className="toolbar">
                <div className={`group i-selection ${realms.length <= 1 ? 'hidden' : ''}`}>
                    <span className="i-button label">Show</span>
                    {realms.map((realm) => (
                        <React.Fragment key={realm.name}>
                            <input type="checkbox"
                                   id={`realm-${realm.name}`}
                                   data-realm={realm.name}
                                   defaultChecked={filters[realm.name]}
                                   onChange={(e) => setFilter({[realm.name]: e.target.checked})} />
                            <label htmlFor={`realm-${realm.name}`} className="i-button">
                                {realm.title}
                            </label>
                        </React.Fragment>
                    ))}
                </div>
                <div className="group">
                    <IButton title="Expand all" classes="icon-stack-plus" />
                    <IButton title="Collapse all" classes="icon-stack-minus" />
                </div>
            </div>
        );
    }
}

Filter.propTypes = {
    realms: PropTypes.arrayOf(PropTypes.object).isRequired,
    filters: PropTypes.object.isRequired,
    setFilter: PropTypes.func.isRequired
};
