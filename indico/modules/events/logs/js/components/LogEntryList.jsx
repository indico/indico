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

import Paginator from 'indico/react/components/Paginator';

function LogEntry({entry}) {
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
                <time dateTime={entry.time}>
                    {moment(entry.time).format('HH:mm')}
                </time>
            </span>
        </li>
    );
}

LogEntry.propTypes = {
    entry: PropTypes.object
};

function LogDate({date, entries}) {
    return (
        <li>
            <h3 className="event-log-day-header">
                {date.format('dddd, D MMMM YYYY')}
            </h3>
            <ul className="event-log-entry-list">
                {entries.map((entry, index) => {
                    return <LogEntry key={index} entry={entry} />;
                })}
            </ul>
        </li>
    );
}

LogDate.propTypes = {
    entries: PropTypes.array,
    date: PropTypes.object
};

export default class LogEntryList extends React.Component {
    render() {
        const {entries, pages, currentPage, changePage} = this.props;

        return (
            <>
                <ul className="event-log-list">
                    {Object.keys(entries).sort().reverse().map(date => {
                        return <LogDate key={date} date={moment(date)} entries={entries[date]} />;
                    })}
                </ul>
                <Paginator currentPage={currentPage} pages={pages}
                           changePage={changePage} />
            </>
        );
    }
}

LogEntryList.propTypes = {
    entries: PropTypes.object,
    page: PropTypes.number,
    changePage: PropTypes.func,
};
