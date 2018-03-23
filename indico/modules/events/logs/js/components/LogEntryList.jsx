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

import {Paginator, TooltipIfTruncated} from 'indico/react/components';

import LogEntryModal from '../containers/LogEntryModal';


class LogEntry extends React.PureComponent {
    static propTypes = {
        entry: PropTypes.object.isRequired,
        setDetailedView: PropTypes.func.isRequired
    };

    constructor(props) {
        super(props);
        this.openDetails = this.openDetails.bind(this);
    }

    openDetails(index) {
        const {setDetailedView} = this.props;
        setDetailedView(index);
    }

    render() {
        const {entry} = this.props;
        return (
            <li className={`log-realm-${entry.type[0]} log-kind-${entry.type[1]}`}>
                <span className="flexrow">
                    <span className="log-icon">
                        <i className="log-realm" />
                        <i className="log-kind icon-circle-small" />
                    </span>
                    <span className="bold">
                        {entry.module}
                    </span>
                </span>
                <TooltipIfTruncated>
                    <span className="log-entry-description"
                          onClick={() => this.openDetails(entry.index)}>
                        {entry.description}
                    </span>
                </TooltipIfTruncated>
                <span className="log-entry-user">
                    {entry.userFullName ? (
                        <TooltipIfTruncated>
                            <span className="user-fullname">
                                <span className="text-superfluous">by </span>
                                {entry.userFullName}
                            </span>
                        </TooltipIfTruncated>
                    ) : ''}
                    <span className="text-superfluous"> at </span>
                    <time dateTime={entry.time}>
                        {moment(entry.time).format('HH:mm')}
                    </time>
                </span>
            </li>
        );
    }
}


function LogDate({date, entries, setDetailedView}) {
    return (
        <li>
            <h3 className="event-log-day-header">
                {date.format('dddd, D MMMM YYYY')}
            </h3>
            <ul className="event-log-entry-list">
                {entries.map((entry) => (
                    <LogEntry key={entry.id} entry={entry} setDetailedView={setDetailedView} />
                ))}
            </ul>
        </li>
    );
}

LogDate.propTypes = {
    entries: PropTypes.array.isRequired,
    date: PropTypes.object.isRequired,
    setDetailedView: PropTypes.func.isRequired
};


export default class LogEntryList extends React.PureComponent {
    static propTypes = {
        entries: PropTypes.array.isRequired,
        entryIndex: PropTypes.instanceOf(Map).isRequired,
        currentPage: PropTypes.number.isRequired,
        pages: PropTypes.array.isRequired,
        changePage: PropTypes.func.isRequired,
        isFetching: PropTypes.bool.isRequired,
        setDetailedView: PropTypes.func.isRequired,
    };

    renderEmpty() {
        return (
            <div className="info-message-box fixed-width">
                <div className="message-box-content">
                    <span className="icon" />
                    <div className="message-text">
                        No logs to show.
                    </div>
                </div>
            </div>
        );
    }

    renderList() {
        const {entries, entryIndex, pages, currentPage, changePage, isFetching, setDetailedView} = this.props;
        return (
            <>
                {isFetching && (
                    <div className="event-log-list-spinner">
                        <div className="i-spinner" />
                    </div>
                )}
                <ul className={`event-log-list ${isFetching ? 'loading' : ''}`}>
                    {[...entryIndex.entries()].map(([date, _entries]) => (
                        <LogDate key={date}
                                 date={moment(date)} entries={_entries}
                                 setDetailedView={setDetailedView} />
                    ))}
                </ul>
                {!isFetching && <Paginator currentPage={currentPage} pages={pages} changePage={changePage} />}
                <LogEntryModal entries={entries} />
            </>
        );
    }

    render() {
        const {entries} = this.props;
        return entries.length ? this.renderList() : this.renderEmpty();
    }
}
