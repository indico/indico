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

import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';

function LogEntry(props) {
    const entry = props.entry;

    return (
        <li className={`log-realm-${entry.type[0]} log-kind-${entry.type[1]}`}>
            <span className="flexrow">
                <span className="log-icon">
                    <i className="log-realm" />
                    <i className="log-kind icon-circle-small" />
                </span>
                <span className="bold f-self-stretch">
                    {entry.module}
                </span>
            </span>
            <span className="log-entry-description">
                {entry.description}
            </span>
            <span>
                {entry.userFullName ? (
                    <span>
                        <span className="text-superfluous">by </span>
                        {entry.userFullName}
                    </span>
                ) : ''}
                <span className="text-superfluous"> at </span>
                <span>
                    {moment(entry.time).format('HH:mm')}
                </span>
            </span>
        </li>
    );
}

LogEntry.propTypes = {
    entry: PropTypes.object
};


export default class LogEntryList extends React.Component {
    render() {
        return (
            <ul className="event-log-list">
                {this.props.entries.map((entry, index) => (
                    <LogEntry key={index} entry={entry} />
                ))}
            </ul>
        );
    }
}

LogEntryList.propTypes = {
    entries: PropTypes.object
};
